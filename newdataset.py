from picamera2 import Picamera2
import cv2
import os
import time
import subprocess
from datetime import datetime

# Ensure the dataset directory exists
SAVE_DIR = "/home/tipqc/Pictures/DATASET/FRESH"
os.makedirs(SAVE_DIR, exist_ok=True)

# Initialize Camera
picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    controls={"FrameRate": 50}
)
picam2.configure(video_config)
picam2.start()

def generate_frames():
    """ Continuously capture frames for preview. """
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

def capture_hdr():
    """ Stops the camera, captures an HDR image using libcamera-still, and restarts the camera. """
    try:
        print("Stopping camera before HDR capture...")
        picam2.stop()
        time.sleep(1)  # Allow time to fully release the camera

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVE_DIR, f"captured_image_{timestamp}.jpg")

        print(f"Capturing HDR image: {filename}")
        subprocess.run([
            "libcamera-still",
            "--hdr",
            "--autofocus-mode", "auto",
            "-o", filename
        ], check=True)

        print(f"Image saved as {filename}")

    except subprocess.CalledProcessError as e:
        print(f"Error capturing HDR image: {e}")

    finally:
        print("Restarting camera...")
        time.sleep(1)  # Small delay before reinitializing
        picam2.configure(video_config)
        picam2.start()
        print("Camera restarted successfully.")

# Flask App
from flask import Flask, Response, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_hdr', methods=['POST'])
def capture_hdr_api():
    """ API endpoint to trigger HDR capture. """
    try:
        capture_hdr()
        return jsonify({"message": "HDR Image Captured Successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
