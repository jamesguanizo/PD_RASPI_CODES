from flask import Flask, Response, request, jsonify
from picamera2 import Picamera2
import cv2
import os
import datetime
import time
import spidev
import pyrebase
from threading import Thread
import math

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

# Constants for MQ136 and MQ137
RL_MQ136 = 20.0  # Load resistance in kOhms for MQ136
RO_MQ136 = 40.0  # Sensor resistance in clean air for MQ136
A_MQ136 = 110.0  # Calibration constant for MQ136
B_MQ136 = -2.7  # Exponent for MQ136

RL_MQ137 = 20.0  # Load resistance in kOhms for MQ137
RO_MQ137 = 200.0  # Sensor resistance in clean air for MQ137
A_MQ137 = 116.6020682  # Calibration constant for MQ137
B_MQ137 = -2.769034857  # Exponent for MQ137

ADC_RESOLUTION = 1023.0  # ADC resolution (10-bit)
VOLTAGE_REF = 5.0  # Reference voltage for MCP3008

def read_adc(channel):
    """Read data from the specified MCP3008 channel (0-7)."""
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be between 0 and 7")
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    value = ((adc[1] & 3) << 8) + adc[2]
    return value

def convert_voltage(data, vref=3.3):
    """Convert raw ADC value to voltage."""
    return data * (vref / 1023.0)

def calculate_ppm(raw_value, RL, RO, A, B):
    """Calculate PPM using calibration constants."""
    if raw_value <= 0:  # Prevent division by zero or invalid input
        return 0
    RS = RL * (ADC_RESOLUTION / raw_value - 1.0)  # Calculate sensor resistance
    ratio = RS / RO  # Calculate RS/RO ratio
    ppm = A * math.pow(ratio, B)  # Calculate PPM using the power-law equation
    return ppm

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
    """Route to save an image from the live feed."""
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
    """Read data from MQ136 and MQ137 and write to Firebase in a loop."""
    while True:
        try:
            raw_value_mq137 = read_adc(2)  # MQ137 connected to channel 2
            raw_value_mq136 = read_adc(0)  # MQ136 connected to channel 0

            # Calculate PPM for MQ137 and MQ136
            ppm_mq137 = calculate_ppm(raw_value_mq137, RL_MQ137, RO_MQ137, A_MQ137, B_MQ137)
            ppm_mq136 = calculate_ppm(raw_value_mq136, RL_MQ136, RO_MQ136, A_MQ136, B_MQ136)

            # Convert raw ADC values to voltage
            voltage_mq137 = convert_voltage(raw_value_mq137)
            voltage_mq136 = convert_voltage(raw_value_mq136)

            # Prepare data for MQ137
            data_mq137 = {
                "ppm": round(ppm_mq137, 2),
                "raw_value": raw_value_mq137,
                "voltage": round(voltage_mq137, 2),
                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Prepare data for MQ136
            data_mq136 = {
                "ppm": round(ppm_mq136, 2),
                "raw_value": raw_value_mq136,
                "voltage": round(voltage_mq136, 2),
                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Write MQ137 data to Firebase
            db.child("mq_sensors").child("MQ137").child("1-set").set(data_mq137)
            db.child("mq_sensors").child("MQ137").child("2-push").push(data_mq137)

            # Write MQ136 data to Firebase
            db.child("mq_sensors").child("MQ136").child("1-set").set(data_mq136)
            db.child("mq_sensors").child("MQ136").child("2-push").push(data_mq136)

            print(f"Data sent to Firebase - MQ137: {data_mq137}, MQ136: {data_mq136}")
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
