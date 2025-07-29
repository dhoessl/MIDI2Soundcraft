from queue import Queue
from threading import Thread, Event
from logging import getLogger
from re import match
from time import sleep
from services.config import Config


class UpdateConfigThread:
    DENIED_OPTIONS = ["digitech", "deesser", "aux", "gate", "eq", "dyn"]
    ALLOWED_INPUT_FUNCTIONS = ["mix", "mute", "solo", "gain"]
    ALLOWED_FX_FUNCTIONS = ["mix", "mute", "bpm"]

    def __init__(
        self,
        update_queue: Queue,
        config: Config,
        logger_name: str = "UpdateConfigThread",
        parent: None = None  # cant specify because it would be circular import
    ) -> None:
        self.logger = getLogger(logger_name)
        self.parent = parent
        self.thread = Thread(
            target=self._thread, args=(update_queue, config)
        )
        self.exit_flag = Event()

    def _thread(self, update_queue: Queue, config: Config) -> None:
        self.logger.info("Starting Update Thread")
        self_init = True
        while not self.exit_flag.is_set():
            if update_queue.qsize() == 0:
                if self_init:
                    self_init = False
                    self.logger.info(
                        "Update Thread init complete"
                        " - Notifications will be send now"
                    )
                sleep(.1)
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
                config.update_channel_fx(
                    msg["channel"], msg["option_channel"],
                    msg["function"], msg["value"]
                )
                if self_init:
                    continue
                self.parent.notify_update(
                    "channel_fx",
                    {
                        "channel": msg["channel"],
                        "fx": msg["option_channel"],
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
                if self_init:
                    continue
                self.parent.notify_update(
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
                if self_init:
                    continue
                self.parent.notify_update("master")
            elif (
                msg["kind"] == "f"
                and "function" in msg
                and (
                    msg["function"] in self.ALLOWED_FX_FUNCTIONS
                    or match(r"^par\d$", msg["function"])
                )
            ):
                if msg["function"] == "bpm":
                    config.update_bpm(msg["value"])
                    if self_init:
                        continue
                    self.parent.notify_update("bpm")
                    continue
                config.update_fx(
                    msg["channel"], msg["function"], msg["value"]
                )
                if self_init:
                    continue
                self.parent.notify_update(
                    "fx",
                    {
                        "channel": msg["channel"],
                        "function": msg["function"]
                    }
                )
            else:
                continue

    def start(self) -> None:
        self.thread.start()

    def join(self) -> None:
        self.thread.join()

    def terminate(self) -> None:
        self.exit_flag.set()
        self.join()
