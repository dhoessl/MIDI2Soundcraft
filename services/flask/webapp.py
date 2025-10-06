from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from os import path
from argparse import Namespace
from loguru import logger

from services.core import ConfigVars, OutputFormatter, Config


class WebApp:
    def __init__(self, args: Namespace, config: Config, secret) -> None:
        service_path = path.split(path.abspath(__file__))[0]
        self.args = args
        self.config = config
        self.vars = ConfigVars()
        self.formatter = OutputFormatter()
        self.app = Flask(
            __name__, root_path=service_path
        )
        self._set_settings(service_path, secret)
        self.socketio = SocketIO(self.app)
        self.provide_paths()
        self.thread_controller = None

    def _set_settings(self, service_path: str, secret: str) -> None:
        self.app.config["SECRET_KEY"] = secret
        self.app.config["APPLICATION_ROOT"] = service_path

    def provide_paths(self) -> None:
        @self.socketio.on("connect")
        def connect() -> None:
            logger.info("New Client connected!")
            if not self.args.test_web:
                self.update_settings({"key": "init"})

        @self.socketio.on("disconnect")
        def disconnect(reason) -> None:
            logger.warning(f"Client disconnected. Reason: {reason}")

        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/favicon.ico")
        def favicon():
            return send_from_directory(
                path.join(self.app.root_path, "static", "favicon"),
                "favicon-96x96.ico", mimetype="image/vnd.microsoft.icon"
            )

    def emit_message(self, key: str, data: str = None) -> None:
        self.socketio.emit(
            "config_update",
            {"key": key, "data": data},
            broadcast=True
        )

    def update_settings(self, msg: dict) -> None:
        if msg["key"] == "bpm":
            self.update_bpm()
        elif msg["key"] == "master":
            self.update_master()
        elif msg["key"] == "channel_fx":
            self.update_channel_fx(
                msg["data"]["channel"],
                msg["data"]["fx"],
                msg["data"]["function"]
            )
        elif msg["key"] == "channel":
            self.update_apc_mix_channel(msg["data"]["channel"])
        elif msg["key"] == "fxmix":
            self.update_fx_return(msg["data"]["channel"])
        elif msg["key"] == "fxpar":
            self.update_fx_params(
                msg["data"]["channel"],
                msg["data"]["function"]
            )
        elif msg["key"] == "channel_move":
            self.update_mix_channels(
                msg["data"]["inc"],
                msg["data"]["index"]
            )
        elif msg["key"] == "fx_move":
            self.update_dial_channels()
        elif msg["key"] == "apc_shift":
            self.set_shift_button(msg["data"]["state"], "apc")
        elif msg["key"] == "midimix_shift":
            self.set_shift_button(msg["data"]["state"], "midimix")
        elif msg["key"] == "matrix_view":
            self.set_apc_side_button(msg["data"]["view"])
        elif msg["key"] == "init":
            for x in range(8):
                self.update_apc_mix_channel(x)
            self.update_dial_channels()
            for x in range(5):
                self.update_fx_params("0", f"par{x + 1}")
            for x in range(4):
                self.update_fx_params("1", f"par{x + 1}")
            for x in range(3):
                self.update_fx_params("2", f"par{x + 1}")
            for x in range(5):
                self.update_fx_params("3", f"par{x + 1}")
            self.update_bpm()
            self.set_apc_side_button("0")
        else:
            pass  # since no logger is active here

    def update_bpm(self) -> None:
        bpm = int(self.config.get_bpm())
        self.emit_message("bpm", f"{bpm}")

    def update_master(self) -> None:
        master = float(self.config.get_master())
        self.emit_message(
            "master",
            {
                "percent": self.vars.soundcraft_to_percent(master),
                "text": self.formatter.mix(master)
            }
        )

    def update_channel_fx(
        self, channel: str | int, fx: str | int, key: str | int
    ) -> None:
        if key != "value":
            return None
        value = float(
            self.config.get_channel_fx_value(
                str(channel), str(fx), str(key)
            )
        )
        self.emit_message(
            "channel_fx",
            {
                "channel": str(channel),
                "fx": str(fx),
                "percent": self.vars.soundcraft_to_percent(value),
                "text": self.formatter.mix(value)
            }
        )

    def update_apc_mix_channel(self, channel: str | int) -> None:
        value_mix = float(self.config.get_channel_value(str(channel), "mix"))
        value_mute = int(self.config.get_channel_value(str(channel), "mute"))
        self.emit_message(
            "channel_mix",
            {
                "channel": str(channel),
                "percent": self.vars.soundcraft_to_percent(value_mix),
                "text": self.formatter.mix(value_mix)
            }
        )
        self.emit_message(
            "channel_mute",
            {
                "channel": str(channel),
                "mute_state": value_mute
            }
        )

    def update_fx_return(self, channel: str | int) -> None:
        value = float(self.config.get_fx_value(str(channel), "mix"))
        self.emit_message(
            "return_fx",
            {
                "channel": str(channel),
                "percent": self.vars.soundcraft_to_percent(value),
                "text": self.formatter.mix(value)
            }
        )

    def set_apc_side_button(self, button_id: int | str) -> None:
        self.emit_message(
            "toggle_apc_side",
            {
                "button": str(button_id)
            }
        )

    def set_shift_button(self, state: bool, controller: str) -> None:
        self.emit_message(
            "shift",
            {
                "state": state,
                "controller": controller
            }
        )

    def update_fx_params(self, channel: str | int, key: str) -> None:
        try:
            delay_time = float(self.config.get_fx_value("1", "par1"))
        except:  # noqa: E722
            delay_time = 1
        try:
            value = float(self.config.get_fx_value(str(channel), key))
            value_slider = self.vars.soundcraft_to_percent(value)
            value_text = self.formatter.fx_parval(
                channel, key, value, delay_time
            )
        except TypeError:
            # Update Thread is sending notifications for
            # non existing parameters since they just get
            # filtered on config level
            # TODO: create filter for notifications too
            return None
        self.emit_message(
            "fx_params",
            {
                "fx": channel,
                "param": key,
                "percent": value_slider,
                "text": value_text
            }
        )

    def update_mix_channels(self, increment: bool, index: int) -> None:
        for channel in range(index, index + 8):
            self.update_apc_mix_channel(index)

    def update_dial_channels(self) -> None:
        data = {}
        for channel in range(12):
            data[channel] = {}
            for fx in range(4):
                value = float(self.config.get_channel_fx_value(
                    str(channel), str(fx), "value"
                ))
                data[channel][fx] = {
                    "value": self.vars.soundcraft_to_percent(value),
                    "text": self.formatter.mix(value)
                }
        self.emit_message("channel_dials", data)
