from flask import Flask, Response, render_template, jsonify
from picamera2 import Picamera2
import cv2
import os
import time
import numpy as np
from inference_sdk import InferenceHTTPClient

# Initialize Flask app
app = Flask(__name__)

# Initialize Camera
picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    controls={"FrameRate": 50}
)
still_config = picam2.create_still_configuration(
    main={"size": (4608, 2592), "format": "RGB888"},
    controls={"NoiseReductionMode": 2}
)

picam2.configure(video_config)
picam2.start()

# Initialize Roboflow Client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="Wk1p4Yv2hc8lK7Of48ME"
)

SAVE_FOLDER = "saved_images"
os.makedirs(SAVE_FOLDER, exist_ok=True)

def draw_boxes(frame, predictions):
    fish_detected = False
    for pred in predictions.get("predictions", []):
        x, y, w, h = int(pred["x"]), int(pred["y"]), int(pred["width"]), int(pred["height"])
        label = f"{pred['class']} ({pred['confidence']:.2f})"
        fish_detected = True
        cv2.rectangle(frame, (x - w // 2, y - h // 2), (x + w // 2, y + h // 2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x - w // 2, y - h // 2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    status_text = "Fish Detected" if fish_detected else "No Fish Detected"
    color = (0, 255, 0) if fish_detected else (0, 0, 255)
    cv2.putText(frame, status_text, (400, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return frame

def generate_frames():
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        result = CLIENT.infer(frame, model_id="fish_detection-z6be1/1")
        frame = draw_boxes(frame, result)
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stream')
def stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_highres', methods=['POST'])
def capture_high_res():
    try:
        picam2.stop()
        time.sleep(1)
        picam2.configure(still_config)
        picam2.start()
        time.sleep(2)
        frame = picam2.capture_array()
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        image_filename = os.path.join(SAVE_FOLDER, f"highres_{timestamp}.jpg")
        _, buffer = cv2.imencode('.jpg', frame)
        with open(image_filename, "wb") as f:
            f.write(buffer.tobytes())
        print(f"Saved high-res image: {image_filename}")
        picam2.stop()
        time.sleep(1)
        picam2.configure(video_config)
        picam2.start()
        return Response(buffer.tobytes(), mimetype='image/jpeg')
    except Exception as e:
        print(f"High-res capture error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
