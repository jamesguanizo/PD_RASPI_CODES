import time
import board
import digitalio
from adafruit_mcp3xxx.mcp3008 import MCP3008
from adafruit_mcp3xxx.analog_in import AnalogIn
import pyrebase
from datetime import datetime

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

# SPI and MCP3008 setup
spi = board.SPI()
cs = digitalio.DigitalInOut(board.D8)  # Chip select pin
mcp = MCP3008(spi, cs)
mq135 = AnalogIn(mcp, 0)  # MQ135 connected to CH0 of MCP3008

print("Sending Data to Firebase Using Raspberry Pi")
print("------------------------------------------")
print()

# Function to prepare data for Firebase with timestamp
def prepare_data(sensor_value, voltage):
    return {
        "raw_value": sensor_value,
        "voltage": round(voltage, 2),  # Round voltage to two decimal places
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Add timestamp
    }

# Write data to Firebase
def write_data_to_firebase(data):
    try:
        # Overwrite existing data with the latest set
        db.child("mq135").child("1-set").set(data)
        # Append new data entry with timestamp
        db.child("mq135").child("2-push").push(data)
        print(f"Data sent: {data}")
    except Exception as e:
        print(f"Error writing to Firebase: {e}")

# Main loop
while True:
    # Read raw value and voltage from MQ135
    sensor_value = mq135.value
    voltage = mq135.voltage

    print(f"Raw Value: {sensor_value}")
    print(f"Voltage: {voltage:.2f} V")
    print()

    # Prepare data with timestamp
    data = prepare_data(sensor_value, voltage)

    # Write data to Firebase
    write_data_to_firebase(data)

    # Delay for 2 seconds
    time.sleep(2)
