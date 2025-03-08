from flask import Flask, Response, request, jsonify
from picamera2 import Picamera2
import cv2
import os
import datetime
import time
import spidev
import pyrebase
from threading import Thread

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

# Firebase configuration
config = {
    "apiKey": "5XGsBXT0nA8c3Do3K9CaLQPjebGWHSLf1Nolq7mz",
    "authDomain": "tryfirebase-a20a3.firebaseapp.com",
    "databaseURL": "https://tryfirebase-a20a3-default-rtdb.firebaseio.com",
    "storageBucket": "tryfirebase-a20a3.appspot.com"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(config)
db = firebase.database()

# Initialize SPI
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_channel(channel):
    """
    Read data from the specified MCP3008 channel (0-7).
    """
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be 0-7")
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def convert_voltage(data, vref=3.3):
    """
    Convert raw ADC value to voltage.
    """
    return data * (vref / 1023.0)

def generate_frames():
    """Generator for video streaming."""
    while True:
        try:
            frame = picam2.capture_array()
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Failed to encode frame")
                continue
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
        frame = picam2.capture_array()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(SAVE_FOLDER, f"image_{timestamp}.jpg")
        cv2.imwrite(file_path, frame)
        print(f"Image saved to: {file_path}")
        return jsonify({"message": "Image saved successfully", "path": file_path}), 200
    except Exception as e:
        print(f"Error saving image: {e}")
        return jsonify({"error": "Failed to save image", "details": str(e)}), 500

def write_data_to_firebase():
    """Read data from MQ135 and write to Firebase in a loop."""
    while True:
        try:
            analog_value = read_channel(0)  # MQ135 AO connected to channel 0
            voltage = convert_voltage(analog_value)
            data = {
                "raw_value": analog_value,
                "voltage": round(voltage, 2),
                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            db.child("mq135").child("1-set").set(data)
            db.child("mq135").child("2-push").push(data)
            print(f"Data sent: {data}")
        except Exception as e:
            print(f"Error writing to Firebase: {e}")
        time.sleep(2)

# Start Firebase data upload in a separate thread
firebase_thread = Thread(target=write_data_to_firebase, daemon=True)
firebase_thread.start()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        spi.close()
