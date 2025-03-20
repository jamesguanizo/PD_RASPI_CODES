from flask import Flask, Response, jsonify
from picamera2 import Picamera2
import cv2
import os
import time

app = Flask(__name__)
picam2 = Picamera2()

# Video mode (Full HD) - Removed autofocus for stability
video_config = picam2.create_video_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    controls={"FrameRate": 50}  # No autofocus
)

# High-resolution capture mode (HDR-ready, reduced resolution)
highres_config = picam2.create_still_configuration(
    main={"size": (2028, 1520), "format": "RGB888"}  # No autofocus
)

SAVE_FOLDER = "saved_images"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Start camera in video mode
picam2.configure(video_config)
picam2.start()

def generate_frames():
    """Video streaming generator function."""
    while True:
        try:
            frame = picam2.capture_array()
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except Exception as e:
            print(f"Frame generation error: {e}")
            break

@app.route('/stream')
def video_feed():
    """Video streaming route."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_highres', methods=['POST'])
def capture_highres():
    """Capture high-resolution image on demand."""
    try:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        image_filename = os.path.join(SAVE_FOLDER, f"highres_{timestamp}.jpg")

        print(f"Capturing high-resolution image: {image_filename}")

        # Switch to high-resolution mode and capture
        picam2.switch_mode_and_capture_file(highres_config, image_filename)

        print(f"Image saved: {image_filename}")

        # Return the captured image
        with open(image_filename, "rb") as f:
            return Response(f.read(), mimetype='image/jpeg')

    except Exception as e:
        print(f"Capture error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
