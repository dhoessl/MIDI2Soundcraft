from queue import Queue
from threading import Thread, Event
from logging import getLogger
from re import match
from services.config import Config


class UpdateConfigThread:
    DENIED_OPTIONS = ["digitech", "deesser", "aux", "gate", "eq", "dyn"]
    ALLOWED_INPUT_FUNCTIONS = ["mix", "mute", "solo", "gain"]
    ALLOWED_FX_FUNCTIONS = ["mix", "mute", "bpm"]

    def __init__(
        self,
        update_queue: Queue,
        apc_queue: Queue,
        midimix_queue: Queue,
        gui_queue: Queue,
        config: Config,
        logger_name: str = "UpdateConfigThread"
    ) -> None:
        self.logger = getLogger(logger_name)
        self.apc_queue = apc_queue
        self.midimix_queue = midimix_queue
        self.qui_queue = gui_queue
        self.thread = Thread(
            target=self._thread, args=(update_queue, config)
        )
        self.exit_flag = Event()

    def _thread(self, update_queue: Queue, config: Config) -> None:
        self.logger.info("Starting Update Thread")
        while not self.exit_flag.is_set():
            if update_queue.qsize() == 0:
                continue

            msg = update_queue.get()
            if msg["kind"] not in ["m", "i", "f"]:
                continue
            elif "option" in msg and msg["option"] in self.DENIED_OPTIONS:
                continue
            elif (
                msg["kind"] == "i"
                and "channel" in msg
                and "option" in msg
                and msg["option"] == "fx"
            ):
                if msg["function"] == "bpm":
                    config.update_bpm(msg["value"])
                    self.notify_update("bpm")
                    continue
                config.update_channel_fx(
                    msg["channel"], msg["options_channel"],
                    msg["function"], msg["value"]
                )
                self.notify_update(
                    "channel_fx",
                    {
                        "channel": msg["channel"],
                        "fx": msg["options_channel"],
                        "function": msg["function"]
                    }
                )
            elif (
                msg["kind"] == "i"
                and "channel" in msg
                and "function" in msg
                and msg["function"] in self.ALLOWED_INPUT_FUNCTIONS
            ):
                config.update_channel(
                    msg["channel"], msg["function"], msg["value"]
                )
                self.notify_update(
                    "channel",
                    {
                        "channel": msg["channel"],
                        "function": msg["function"]
                    }
                )
            elif (
                msg["kind"] == "m"
                and "channel" in msg
                and msg["channel"] == "mix"
            ):
                config.update_master(msg["value"])
                self.notify_update("master")
            elif (
                msg["kind"] == "f"
                and "function" in msg
                and (
                    msg["function"] in self.ALLOWED_FX_FUNCTIONS
                    or match(r"^par\d$", msg["function"])
                )
            ):
                config.update_fx(
                    msg["channel"], msg["functions"], msg["value"]
                )
                self.notify_update(
                    "fx",
                    {
                        "channel": msg["channel"],
                        "function": msg["function"]
                    }
                )
            else:
                continue

    def notify_update(self, key: str, data: dict = {}) -> None:
        if key == "bpm":
            self.gui_queue.put({"key": key})
        elif key == "channel_fx":
            self.gui_queue.put({"key": key, "data": data})
        elif key == "channel":
            self.gui_queue.put({"key": key, "data": data})
            self.apc_queue.put({"key": key, "data": data})
        elif key == "master":
            self.gui_queue.put({"key": key})
            self.apc_queue.put({"key": key})
        elif key == "fx":
            if data["function"] == "mix":
                self.apc_queue.put({"key": "fxmix", "data": data})
                self.gui_queue.put({"key": "fxmix", "data": data})
            elif "par" in data["function"]:
                self.gui_queue.put({"key": "fxpar", "data": data})
        else:
            return None

    def start(self) -> None:
        self.thread.start()

    def join(self) -> None:
        self.thread.join()

    def terminate(self) -> None:
        self.exit_flag.set()
        self.join()
