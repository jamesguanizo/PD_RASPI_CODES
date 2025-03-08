from flask import Flask, Response, request, jsonify
from picamera2 import Picamera2
import cv2
import os
import datetime

app = Flask(__name__)
picam2 = Picamera2()

# Configure the camera for video streaming
try:
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480), "format": "RGB888"}))
    picam2.set_controls({"FrameRate": 15})
    picam2.start()
except Exception as e:
    print(f"Error configuring camera: {e}")
    picam2.close()

# Folder to save images
SAVE_FOLDER = "saved_images"
os.makedirs(SAVE_FOLDER, exist_ok=True)

def generate_frames():
    """Generator for video streaming."""
    while True:
        try:
            # Capture frame-by-frame
            frame = picam2.capture_array()
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Failed to encode frame")
                continue

            # Convert to byte format for MJPEG streaming
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"Error generating frame: {e}")
            break

@app.route('/stream')
def video_feed():
    """Route for video streaming."""
    try:
        return Response(generate_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        print(f"Error in video_feed: {e}")
        return "Streaming error", 500

@app.route('/save_image', methods=['POST'])
def save_image():
    """
    Route to capture an image from the live camera feed
    and save it to the Raspberry Pi's local storage.
    """
    try:
        # Capture the current frame from the camera
        frame = picam2.capture_array()
        
        # Generate a timestamped filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(SAVE_FOLDER, f"image_{timestamp}.jpg")
        
        # Save the image to the specified path
        cv2.imwrite(file_path, frame)
        
        print(f"Image saved to: {file_path}")
        return jsonify({"message": "Image saved successfully", "path": file_path}), 200
    except Exception as e:
        print(f"Error saving image: {e}")
        return jsonify({"error": "Failed to save image", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
