import numpy as np
import cv2 as cv
import scipy.ndimage as ndi
import operator
import sys


def process(image):
    lower = np.uint8([18, 94, 140])
    upper = np.uint8([48, 255, 255])
    white_mask = cv.inRange(image, lower, upper)
    # yellow color mask
    lower = np.uint8([18, 94, 140])
    upper = np.uint8([48, 255, 255])
    yellow_mask = cv.inRange(image, lower, upper)
    # combine the mask
    gray = cv.cvtColor(image, cv.COLOR_BGR2HSV)

    # mask = cv.bitwise_or(white_mask, yellow_mask)
    # masked = cv.bitwise_and(image, image, mask=mask)

    # convert to grayscale
    # gray = cv.cvtColor(masked, cv.COLOR_RGB2GRAY)

    # convert to hsv

    # detect edges using Canny Method then straight lines using Hough Lines Probablistic
    lines = cv.HoughLinesP(
        (cv.Canny(gray, 50, 200)),
        rho=1,
        theta=np.pi / 180,
        threshold=50,
        maxLineGap=1,
        minLineLength=30,
    )

    # draw the lines on a copy of the image

    new_img = np.copy(image)
    lines_list = []

    for points in lines:
        x, y, x1, y1 = points[0]
        cv.line(new_img, (x, y), (x1, y1), (0, 0, 255), 2)

        lines_list.append([(x, y), (x1, y1)])

    return lines


def blocks(image, lines):

    new_image = np.copy(image)

    # Step 1: Create a clean list of lines
    cleaned = []
    for line in lines:
        for x1, y1, x2, y2 in line:
            if abs(y2 - y1) <= 1 and abs(x2 - x1) >= 25 and abs(x2 - x1) <= 55:
                cleaned.append((x1, y1, x2, y2))

    # Step 2: Sort cleaned by x1 position
    list1 = sorted(cleaned, key=operator.itemgetter(0, 1))

    # Step 3: Find clusters of x1 close together - clust_dist apart
    clusters = {}
    dIndex = 0
    clus_dist = 10

    for i in range(len(list1) - 1):
        distance = abs(list1[i + 1][0] - list1[i][0])
        #         print(distance)
        if distance <= clus_dist:
            if not dIndex in clusters.keys():
                clusters[dIndex] = []
            clusters[dIndex].append(list1[i])
            clusters[dIndex].append(list1[i + 1])

        else:
            dIndex += 1

    # Step 4: Identify coordinates of rectangle around this cluster
    rects = {}
    i = 0
    for key in clusters:
        all_list = clusters[key]
        cleaned = list(set(all_list))
        if len(cleaned) > 5:
            cleaned = sorted(cleaned, key=lambda tup: tup[1])
            avg_y1 = cleaned[0][1]
            avg_y2 = cleaned[-1][1]
            #         print(avg_y1, avg_y2)
            avg_x1 = 0
            avg_x2 = 0
            for tup in cleaned:
                avg_x1 += tup[0]
                avg_x2 += tup[2]
            avg_x1 = avg_x1 / len(cleaned)
            avg_x2 = avg_x2 / len(cleaned)
            rects[i] = (avg_x1, avg_y1, avg_x2, avg_y2)
            i += 1

    print("Num Parking Lanes: ", len(rects))
    # Step 5: Draw the rectangles on the image
    buff = 7
    for key in rects:
        tup_topLeft = (int(rects[key][0] - buff), int(rects[key][1]))
        tup_botRight = (int(rects[key][2] + buff), int(rects[key][3]))
        #         print(tup_topLeft, tup_botRight)
        cv.rectangle(new_image, tup_topLeft, tup_botRight, (0, 255, 0), 3)

    return new_image, rects


# MAIN
pwd = sys.path[0]
image = cv.imread(pwd + "/Assets/overhead_parking.png")


# image = cv.imread("Assets/overhead_parking.png")

rect_coords = []

new_image, rects = blocks(image, process(image))
rect_coords.append(rects)

while True:
    cv.imshow("Processed", new_image)

    key = cv.waitKey(1)

    if key == 27:
        break


cv.destroyAllWindows()
