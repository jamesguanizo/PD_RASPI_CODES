from flask import Flask, Response, jsonify
from picamera2 import Picamera2
import cv2
import os
import time
import numpy as np

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

def zoom_image(image, zoom_factor=2.0):
    """Zoom into the center of the image by a given factor."""
    height, width, _ = image.shape

    # Compute the cropping window
    new_width = int(width / zoom_factor)
    new_height = int(height / zoom_factor)
    x1 = (width - new_width) // 2
    y1 = (height - new_height) // 2
    x2 = x1 + new_width
    y2 = y1 + new_height

    # Crop and resize back to original size
    cropped = image[y1:y2, x1:x2]
    zoomed = cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LINEAR)

    return zoomed

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
    """Capture high-resolution image and apply zoom effect."""
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

        # Apply zoom
        zoomed_frame = zoom_image(frame, zoom_factor=2.0)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        image_filename = os.path.join(SAVE_FOLDER, f"zoomed_{timestamp}.jpg")

        # Encode the image into JPEG format
        _, buffer = cv2.imencode('.jpg', zoomed_frame)
        if not _:
            raise ValueError("Failed to encode image")

        # Save the image
        with open(image_filename, "wb") as f:
            f.write(buffer.tobytes())

        print(f"Saved zoomed image: {image_filename}")

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
