#!/root/midi_controller/bin/python3
from services.controller import Controller

if __name__ == "__main__":
    controller = Controller("10.10.1.1", "10.10.1.10")
    controller.run()
