from flask import Flask, Response, render_template
from picamera2 import Picamera2
import cv2
import numpy as np
from inference_sdk import InferenceHTTPClient

# Initialize Flask app
app = Flask(__name__)

# Initialize the Camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

# Initialize Roboflow Client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="Wk1p4Yv2hc8lK7Of48ME"
)

def draw_boxes(frame, predictions):
    """Draws bounding boxes on the frame based on the detection results."""
    fish_detected = False  # Flag to track detection status
    
    for pred in predictions.get("predictions", []):
        x, y, w, h = int(pred["x"]), int(pred["y"]), int(pred["width"]), int(pred["height"])
        label = f"{pred['class']} ({pred['confidence']:.2f})"
        fish_detected = True  # Fish detected

        # Draw bounding box
        cv2.rectangle(frame, (x - w // 2, y - h // 2), (x + w // 2, y + h // 2), (0, 255, 0), 2)

        # Draw label
        cv2.putText(frame, label, (x - w // 2, y - h // 2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Draw "No Fish Detected" or "Fish Detected" in the upper right corner
    status_text = "Fish Detected" if fish_detected else "No Fish Detected"
    color = (0, 255, 0) if fish_detected else (0, 0, 255)
    cv2.putText(frame, status_text, (400, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    return frame

def generate_frames():
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for OpenCV

        # Perform object detection
        result = CLIENT.infer(frame, model_id="fish_detection-z6be1/1")
        frame = draw_boxes(frame, result)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stream')
def stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
