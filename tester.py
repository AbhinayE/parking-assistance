import eel
import threading

eel.init("frontend")


def gui():
    eel.start(
        "direction.html",
        size=(600, 600),
    )


t1 = threading.Thread(target=gui)
t1.start()


eel.myFunc(1, 2)
