from flask import Flask, Response, render_template, jsonify
from picamera2 import Picamera2
import cv2
import os
import time
import threading
import numpy as np
from inference_sdk import InferenceHTTPClient

# Initialize Flask app
app = Flask(__name__)

# Initialize Camera
picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": (1280, 720), "format": "YUV420"},  # Reduced resolution & switched to YUV420
    controls={"FrameRate": 30}  # Lowered frame rate for better performance
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

# Global variable for inference results
result_cache = None

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
    cv2.putText(frame, status_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    return frame

def run_inference(frame):
    """Runs inference in a separate thread to prevent blocking the main process."""
    global result_cache
    result_cache = CLIENT.infer(frame, model_id="fish_detection-z6be1/1")

def generate_frames():
    """Generates video frames with real-time inference."""
    global result_cache
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)  # Convert YUV to BGR for OpenCV
        
        # Run inference asynchronously
        threading.Thread(target=run_inference, args=(frame,)).start()

        # Use cached inference result
        frame = draw_boxes(frame, result_cache if result_cache else {"predictions": []})

        # Encode frame as JPEG
        ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               jpeg.tobytes() + b'\r\n')

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
    """Captures a high-resolution image and saves it."""
    try:
        picam2.stop()
        time.sleep(1)
        picam2.configure(still_config)
        picam2.start()
        time.sleep(2)
        frame = picam2.capture_array()

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        image_filename = os.path.join(SAVE_FOLDER, f"highres_{timestamp}.jpg")

        # Save high-res image
        _, buffer = cv2.imencode('.jpg', frame)
        with open(image_filename, "wb") as f:
            f.write(buffer.tobytes())

        print(f"Saved high-res image: {image_filename}")

        # Switch back to video mode
        picam2.stop()
        time.sleep(1)
        picam2.configure(video_config)
        picam2.start()

        return Response(buffer.tobytes(), mimetype='image/jpeg')
    except Exception as e:
        print(f"High-res capture error: {e}")
        return jsonify({"error": str(e)}), 500

@app.after_request
def add_header(response):
    """Improves stream buffering by preventing unnecessary caching."""
    response.headers["Cache-Control"] = "no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
