from subprocess import Popen, PIPE, run
from time import sleep
from logging import getLogger


def wait_connect(
    skip_check: bool = False,
    logger_name: str = "networking"
) -> None:
    # Dirty Quickfix
    logger = getLogger(logger_name)
    soundcraft_network_name = run(
        "nmcli con show | grep -i 'soundcraft' | awk -F'  ' '{ printf $1 }'",
        shell=True, capture_output=True
    ).stdout.decode().split("\n")[0]
    if not soundcraft_network_name:
        soundcraft_network_name = "soundcraft"
    check_network = Popen(
        [
            "nmcli", "-f", "GENERAL.STATE",
            "con", "show", f"{soundcraft_network_name}"
        ],
        stdout=PIPE,
        stderr=PIPE
    )
    outputstd = b''
    while 'activated' not in outputstd.decode():
        # Waiting till nmcli connection to soundcraft is up
        outputstd, outputstderr = check_network.communicate()
        sleep(.5)
        logger.warning("Waiting for soundcraft Wifi...")
        if skip_check:
            logger.error("Wifi Check is skipped")
            outputstd = b"activated"
    logger.debug(
        "Connection to Soundcraft Wifi exists"
    )
    return True
