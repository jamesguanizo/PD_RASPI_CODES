from flask import Flask, Response, jsonify, request, send_file
from picamera2 import Picamera2
import cv2
import os
import datetime
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

SAVE_FOLDER = "saved_images"
os.makedirs(SAVE_FOLDER, exist_ok=True)

picam2 = None

def initialize_camera():
    """Initializes the Raspberry Pi camera."""
    global picam2
    if picam2 is None:
        try:
            picam2 = Picamera2()
            picam2.configure(picam2.create_video_configuration(main={"size": (640, 480), "format": "RGB888"}))
            picam2.start()
        except Exception as e:
            print(f"Error initializing camera: {e}")

def cleanup_camera():
    """Releases the camera resources."""
    global picam2
    if picam2:
        picam2.close()
        picam2 = None

@app.route('/stream')
def video_feed():
    """Streams video from the Raspberry Pi camera."""
    def generate_frames():
        while True:
            if picam2:
                frame = picam2.capture_array()
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            else:
                time.sleep(0.1)
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/save_image', methods=['POST'])
def save_image():
    """Captures an image and sends it to the client."""
    try:
        if picam2:
            frame = picam2.capture_array()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(SAVE_FOLDER, f"image_{timestamp}.jpg")
            cv2.imwrite(file_path, frame)
            return jsonify({"message": "Image captured", "path": file_path}), 200
        else:
            return jsonify({"error": "Camera not initialized"}), 500
    except Exception as e:
        return jsonify({"error": "Failed to capture image", "details": str(e)}), 500

@app.route('/download_image', methods=['GET'])
def download_image():
    """Allows the client to download the last saved image."""
    try:
        files = sorted(os.listdir(SAVE_FOLDER), reverse=True)
        if files:
            latest_file = os.path.join(SAVE_FOLDER, files[0])
            return send_file(latest_file, as_attachment=True)
        else:
            return jsonify({"error": "No images available"}), 404
    except Exception as e:
        return jsonify({"error": "Failed to download image", "details": str(e)}), 500

if __name__ == '__main__':
    try:
        initialize_camera()
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        cleanup_camera()
