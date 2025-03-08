from flask import Flask, Response, jsonify
from picamera2 import Picamera2
import cv2
import os
import time

app = Flask(__name__)
picam2 = Picamera2()

# Camera configurations
video_config = picam2.create_video_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    controls={"FrameRate": 50}
)

still_config = picam2.create_still_configuration(
    main={"size": (4608, 2592), "format": "RGB888"},
    controls={"NoiseReductionMode": 2}  # Removed HDR, as it is not supported
)

# Start in video mode
picam2.configure(video_config)
picam2.start()

SAVE_FOLDER = "saved_images"
os.makedirs(SAVE_FOLDER, exist_ok=True)

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
def capture_high_res():
    """Capture high-resolution image on demand."""
    try:
        # Stop video mode
        picam2.stop()
        time.sleep(1)  # Allow buffer clear

        # Switch to still mode
        picam2.configure(still_config)
        picam2.start()
        time.sleep(2)  # Allow camera to adjust

        # Capture image
        frame = picam2.capture_array()
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        image_filename = os.path.join(SAVE_FOLDER, f"highres_{timestamp}.jpg")

        # Encode the image into JPEG format
        _, buffer = cv2.imencode('.jpg', frame)
        if not _:
            raise ValueError("Failed to encode image")

        # Save the image
        with open(image_filename, "wb") as f:
            f.write(buffer.tobytes())

        print(f"Saved high-res image: {image_filename}")

        # Switch back to video mode
        picam2.stop()
        time.sleep(1)  # Allow transition
        picam2.configure(video_config)
        picam2.start()

        # Return image in the response
        return Response(buffer.tobytes(), mimetype='image/jpeg')

    except Exception as e:
        print(f"High-res capture error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
