import sys
from matplotlib.style import available
import numpy as np
import pickle
import cv2
import cvzone
from pathlib import Path
import eel
import threading

# Global vars
VIDEO_LOCATION = str(Path("data/reversed.mp4"))
WIDTH, HEIGHT = 107, 48


try:
    with open("compDict.p", "rb") as x:
        mainDict = pickle.load(x)
        Dict = mainDict
except FileNotFoundError:
    sys.exit("Run Slots.py first to generate slots to watch")


def process(feed):

    # the image has been converted to grayscale and blurred
    processed = cv2.GaussianBlur((cv2.cvtColor(feed, cv2.COLOR_BGR2GRAY)), (3, 3), 1)

    # converting to binary image map
    threshold = cv2.adaptiveThreshold(
        processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16
    )

    # applying median blur to reduce noise
    median = cv2.medianBlur(threshold, 5)

    # stretching the pixels in the image to make it easier to find bounds

    kernels = np.ones((3, 3), np.uint8)

    dilate = cv2.dilate(median, kernels, iterations=1)

    return dilate


def checkSlot(processed):
    emptyLots = []
    availableSlots = 0
    for x in Dict.values():
        a, b = x["pos"]
        slot = processed[b : b + HEIGHT, a : a + WIDTH]

        # counting all non-zero pixels
        count = cv2.countNonZero(slot)

        # showing non-zero pixel count
        # cvzone.putTextRect(
        #     feed, str(count), (a + 10, b + 10), 1, 1, (255, 255, 255), (0, 0, 0)
        # )
        if count < 800:
            # change the slot occupancy if empty
            color = [0, 255, 0]
            availableSlots += 1
            thickness = 2
            x["occupied"] = False
        else:
            x["occupied"] = True
            color = [255, 255, 255]
            thickness = 1

        # print(Dict)

        cv2.rectangle(feed, (a, b), (a + WIDTH, b + HEIGHT), color, thickness)

        if x["occupied"] == False:

            # get distances of the empty lots and store them in a list
            emptyLots.append(x["distance"])

            # return minimum value
            minDistance = min(emptyLots)

            # print(minDistance)
        # get key of closest empty lot
    suggested = [k for k in Dict if (Dict[k]["distance"] == minDistance)]

    cvzone.putTextRect(
        feed,
        f"Free:{availableSlots}/{len(Dict)}",
        (50, 50),
        scale=2,
        thickness=1,
        offset=3,
        colorR=[255, 255, 255],
        colorT=[0, 0, 0],
    )

    # Call the js function to update the slots.
    eel.myFunc(int(availableSlots), int(len(Dict)), int(suggested[0]))

    # print(suggested)

    # Show nearest unoccupied slot
    cvzone.putTextRect(
        feed,
        f"Nearest Lot: {str(suggested[0])}",
        (800, 60),
        scale=2,
        thickness=1,
        offset=2,
        colorR=[255, 255, 255],
        colorT=[0, 0, 0],
    )


# front end rendering using eel on a separate thread
def renderer():
    eel.start(
        "direction.html",
        size=(1000, 800),
    )


cap = cv2.VideoCapture(VIDEO_LOCATION)
eel.init("frontend")


t1 = threading.Thread(
    target=renderer,
)
t1.start()

# eel.spawn(renderer)


while True:
    count = 1
    # looping the video
    if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    _, feed = cap.read()
    checkSlot(process(feed))

    for x in Dict.values():
        # lot indexes
        cvzone.putTextRect(
            feed,
            str(count),
            (
                x["pos"][0] + 5,
                x["pos"][1] + 15,
            ),
            scale=1,
            thickness=1,
            offset=2,
            colorR=[255, 255, 255],
            colorT=[0, 0, 0],
        )

        # distance to gate
        cvzone.putTextRect(
            feed,
            f"Distance: {x['distance']}",
            (
                x["pos"][0] + 35,
                x["pos"][1] + 45,
            ),
            scale=0.7,
            thickness=1,
            offset=2,
            colorR=[255, 255, 255],
            colorT=[0, 0, 0],
        )

        count += 1

        # show the nearest unoccupied lot

    cv2.imshow("Parking Lot Feed", feed)
    key = cv2.waitKey(10)

    if key == 27:
        break
