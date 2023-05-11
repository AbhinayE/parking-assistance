import pickle
from pathlib import Path
import cv2
import pickle
import cvzone
import math
import os
import random

WIDTH, HEIGHT = 107, 48
GATE = (42, 13)

# removing previous files to start on a clean slate
try:
    os.remove("data/slots.p")
    os.remove("compDict.p")
except FileNotFoundError:
    pass

Dict = dict()
nodePos = []


def mouseCLick(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        nodePos.append((x, y))
        with open("data/slots.p", "wb") as f:
            pickle.dump(nodePos, f)

    if event == cv2.EVENT_RBUTTONDOWN:
        for i, pos in enumerate(nodePos):
            x1, y1 = pos
            if x1 < x < (x1 + WIDTH) and y1 < y < (y1 + HEIGHT):
                nodePos.pop(i)
                Dict.pop(i + 1)

        with open("data/slots.p", "wb") as f:
            pickle.dump(nodePos, f)

    getDistance(nodePos)


def getDistance(nodePos):
    index = []
    index.extend(range(1, len(nodePos)))

    i = 1

    for x in nodePos:
        Dict[i] = {
            "pos": x,
            "distance": abs(math.floor(x[0] + (WIDTH / 2)) - GATE[0])
            + abs((math.floor(x[1] + (HEIGHT / 2)) - GATE[1])),
            "occupied": True,
            "latitude": random.uniform(-90, 90),  # Random latitude
            "longitude": random.uniform(-180, 180),  # Random longitude
        }

        if i != 69:
            i = i + 1
        else:
            break


def drawRects(nodes):

    count = 1
    for x in nodes:
        # Drawing rectangles
        cv2.rectangle(
            img,
            x,
            (x[0] + WIDTH, x[1] + HEIGHT),
            [255, 255, 255],
            1,
        )

        # drawing lot indexes
        cvzone.putTextRect(
            img,
            str(count),
            (
                x[0] + 5,
                x[1] + 15,
            ),
            scale=1,
            thickness=1,
            offset=2,
            colorR=[255, 255, 255],
            colorT=[0, 0, 0],
        )

        # distance to gate
        cvzone.putTextRect(
            img,
            f"Distance: {abs(math.floor(x[0] + (WIDTH / 2)) - GATE[0])+ abs((math.floor(x[1] + (HEIGHT / 2)) - GATE[1]))}",
            (
                x[0] + 35,
                x[1] + 45,
            ),
            scale=0.7,
            thickness=1,
            offset=2,
            colorR=[255, 255, 255],
            colorT=[0, 0, 0],
        )
        count += 1


def close():
    with open("compDict.p", "wb") as f:
        pickle.dump(Dict, f)


if __name__ == "__main__":
    while True:
        count = 1
        img = cv2.imread(str(Path("data/overhead_parking.png")))

        drawRects(nodePos)
        cv2.imshow("out", img)
        cv2.setMouseCallback("out", mouseCLick)

        key = cv2.waitKey(1)

        if key == 27:
            close()
            break
