from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from os import path


class WebApp:
    def __init__(self, logger, args, config) -> None:
        service_path = path.join(
            path.split(path.abspath(__file__))[0],
            "flask"
        )
        self.config = config
        self.app = Flask(
            __name__, root_path=service_path
        )
        self._set_settings(service_path)
        self.socketio = SocketIO(self.app)
        self.provide_paths()
        self.thread_controller = None

    def _set_settings(self, service_path) -> None:
        self.app.config["SECRET_KEY"] = "test!secrect"
        self.app.config["APPLICATION_ROOT"] = service_path

    def provide_paths(self) -> None:
        @self.socketio.on("connect")
        def connect(self) -> None:
            print("New Client connected. Sending config")
            emit("init_config", {"msg": "dies das ananas"})

        @self.socketio.on("disconnect")
        def disconnect(reason) -> None:
            print(f"Client disconnected. Reason: {reason}")

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
        emit(
            "config_update",
            {"key": key, "data": data}
        )

    def update_settings(self, msg: dict) -> None:
        if msg["key"] == "bpm":
            self.update_bpm()
        elif msg["key"] == "channel_fx":
            self.update_channel_fx(
                msg["data"]["channel"],
                msg["data"]["fx"],
                msg["data"]["function"]
            )
        elif msg["key"] == "channel":
            self.update_apc_mix_channel(msg["data"]["channel"])
        elif msg["key"] == "master":
            self.update_master()
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
        # TODO: make it %
        self.emit_message("bpm", f"{bpm}")

    def update_master(self) -> None:
        master = float(self.config.get_master())
        self.emit_message("master", f"{master}")

    def update_channel_fx(
        self,
        channel: str | int,
        fx: str | int,
        key: str | int
    ) -> None:
        if key != "value":
            return None
        value = float(self.config.get_channel_fx_value(
            str(channel), str(fx), str(key)
        ))
        self.gui.change_dial_value(
            int(channel), int(fx),
            int(round(float(self.vars.soundcraft127(value)), 0)),
            self.formatter.mix(value)
        )

    def update_apc_mix_channel(self, channel: str | int) -> None:
        value_mix = float(self.config.get_channel_value(str(channel), "mix"))
        value_mute = int(self.config.get_channel_value(str(channel), "mute"))
        self.gui.set_apc_channel_value(
            int(channel), self.vars.soundcraft_to_midi(value_mix),
            self.formatter.mix(value_mix)
        )
        self.gui.set_apc_mute_button(int(channel), value_mute)

    def update_fx_return(self, channel: str | int) -> None:
        value = float(self.config.get_fx_value(str(channel), "mix"))
        self.gui.set_apc_channel_value(
            int(channel), self.vars.soundcraft_to_midi(value),
            self.formatter.mix(value)
        )

    def set_apc_side_button(self, button_id: int | str) -> None:
        self.gui.set_apc_side_button(int(button_id))

    def set_shift_button(self, state: bool, controller: str) -> None:
        self.gui.set_shift_button(state, controller)

    def update_fx_params(self, channel: str | int, key: str) -> None:
        try:
            delay_time = float(self.config.get_fx_value("1", "par1"))
        except:  # noqa: E722
            delay_time = 1
        try:
            value = float(self.config.get_fx_value(str(channel), key))
            value_slider = round(float(self.vars.soundcraft127(value)), 0)
            value_text = self.formatter.fx_parval(
                channel, key, value, delay_time
            )
        except TypeError:
            # Update Thread is sending notifications for
            # non existing parameters since they just get
            # filtered on config level
            # TODO: create filter for notifications too
            return None
        if int(channel) == 0:
            self.gui.change_apc_slider_value(
                int(key[-1:]) - 1,
                value_slider, value_text
            )
        elif int(channel) == 1:
            self.gui.change_apc_slider_value(
                int(key[-1:]) + 4,
                value_slider, value_text
            )
        elif int(channel) == 2:
            self.gui.change_midimix_slider_value(
                int(key[-1:]) - 1,
                value_slider, value_text
            )
        elif int(channel) == 3:
            self.gui.change_midimix_slider_value(
                int(key[-1:]) + 2,
                value_slider, value_text
            )

    def update_mix_channels(self, increment: bool, index: int) -> None:
        for channel in range(index, index + 8):
            self.update_apc_mix_channel(index)
        # data = {}
        # for channel in range(index, index + 8):
        #     value_mix = float(
        #         self.config.get_channel_value(str(channel), "mix")
        #     )
        #     data[channel] = {
        #         "btns": self.vars.soundcraft_to_midi(value_mix),
        #         "value": self.formatter.mix(value_mix),
        #     }
        # self.gui.change_apc_channels(increment, data)
        # for lower_button in range(index, 8 + index):
        #     mute_values = []
        #     mute_values.append(
        #         int(self.config.get_channel_value(str(lower_button), "mute"))
        #     )
        # for val in mute_values:
        #     self.gui.set_apc_mute_button(mute_values.index(val), bool(val))

    def update_dial_channels(self) -> None:
        data = {}
        for channel in range(12):
            data[channel] = {}
            for fx in range(4):
                value = float(self.config.get_channel_fx_value(
                    str(channel), str(fx), "value"
                ))
                data[channel][fx] = {
                    "value": round(float(self.vars.soundcraft127(value)), 0),
                    "label": self.formatter.mix(value)
                }
        self.gui.change_dial_channels(data)
        pass
