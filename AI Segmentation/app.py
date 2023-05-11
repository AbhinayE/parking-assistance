import cv2
from flask import Flask, render_template, Response

from pathlib import Path


app = Flask(__name__)

def generate_video_stream(video_location):
    cap = cv2.VideoCapture(video_location)
    while True:
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        _, frame = cap.read()
        checkSlot(process(frame))
        # Encode the frame as JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')


@app.route('/video_feed')


def video_feed():
    VIDEO_LOCATION = str(Path("data/overhead_parking.mp4"))
    return Response(generate_video_stream(VIDEO_LOCATION),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
