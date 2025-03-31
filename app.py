#!/root/midi_controller/bin/python3
from services.controller import Controller
from subprocess import Popen, PIPE
from time import sleep

if __name__ == "__main__":
    check_network = Popen(
        ["nmcli", "-f", "GENERAL.STATE", "con", "show", "soundcraft"],
        stdout=PIPE,
        stderr=PIPE
    )
    stdout = b''
    while 'activated' not in stdout.decode():
        # Waiting till nmcli connection to soundcraft is up
        stdout, stderr = check_network.communicate()
        sleep(.5)
    controller = Controller("10.10.1.1", "10.10.1.10")
    controller.run()
