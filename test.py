import sys
import numpy as np
import pickle
import cv2
import cvzone
from pathlib import Path
from flask import jsonify

from flask import Flask, render_template, Response, request, redirect, url_for, flash, session

from flask_sqlalchemy import SQLAlchemy

# Global vars
VIDEO_LOCATION = str(Path("data/overhead_parking.mp4"))
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

def checkSlot(feed, processed):
    emptyLots = []
    availableSlots = 0
    for x in Dict.values():
        a, b = x["pos"]
        slot = processed[b : b + HEIGHT, a : a + WIDTH]

        # counting all non-zero pixels
        count = cv2.countNonZero(slot)

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

        cv2.rectangle(feed, (a, b), (a + WIDTH, b + HEIGHT), color, thickness)

        if x["occupied"] == False:
            # get distances of the empty lots and store them in a list
            emptyLots.append(x["distance"])

            # return minimum value
            minDistance = min(emptyLots)

    suggested = [k for k in Dict if (Dict[k]["distance"] == minDistance)]

    global nearest_slot, google_maps_link
    nearest_slot = suggested[0]
    print(nearest_slot)
    google_maps_link = f"https://www.google.com/maps?q={Dict[nearest_slot]['latitude']},{Dict[nearest_slot]['longitude']}"


    with open("link.txt", "w") as f:
        f.write(google_maps_link)


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

    # Show nearest unoccupied slot
    cvzone.putTextRect(
        feed,
        f"Nearest Lot: {str(suggested[0])} ({google_maps_link})",
        (800, 60),
        scale=0.5,
        thickness=1,
        offset=2,
        colorR=[255, 255, 255],
        colorT=[0, 0, 0],
    )
    return google_maps_link, suggested[0]

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.secret_key = 'mysecretkey'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

with app.app_context():
    db.create_all()


google_maps_link = ""
nearest_slot = 0

def generate_video_stream(video_location):
    cap = cv2.VideoCapture(video_location)
    while True:
        count=1
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        _, frame = cap.read()
        processed_frame = process(frame)
        google_maps_link, nearest_slot = checkSlot(frame, processed_frame)
        for x in Dict.values():
            # lot indexes
            cvzone.putTextRect(
                frame,
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
                frame,
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
        # Encode the frame as JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
       

@app.route('/video_feed')
def video_feed():
    return Response(generate_video_stream(VIDEO_LOCATION),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')



@app.route("/get_google_maps_link")
def get_google_maps_link():
    return google_maps_link


@app.route('/nearest_slot')
def nearest_slot():
    return str(nearest_slot)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first() is not None:
            flash('Username already exists. Choose a different one.')
            return redirect(url_for('signup'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)