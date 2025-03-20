from picamera2 import Picamera2
import cv2
import os
import subprocess
import time
from datetime import datetime

# Ensure the dataset directory exists
save_dir = "/home/tipqc/Pictures/DATASET/FRESH"
os.makedirs(save_dir, exist_ok=True)

# Initialize the camera
picam2 = Picamera2()
camera_config = picam2.create_still_configuration()
picam2.configure(camera_config)

# Start the camera preview
picam2.start_preview()
picam2.start()

print("Press SPACEBAR to capture an HDR image with autofocus, ESC to exit.")

while True:
    # Capture a preview frame
    frame = picam2.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imshow("Camera Preview", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == 32:  # Spacebar (Capture HDR Image)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(save_dir, f"captured_image_{timestamp}.jpg")

        print("Pausing picamera2 to free the camera...")
        picam2.stop()
        time.sleep(2)  # Allow full camera release before HDR capture

        print(f"Capturing HDR image: {filename}")
        try:
            subprocess.run([
                "libcamera-still",
                "--hdr",
                "--autofocus-mode", "auto",
                "-o", filename
            ], check=True)
            print(f"Image saved as {filename}")
        except subprocess.CalledProcessError as e:
            print(f"Error capturing HDR image: {e}")

        print("Restarting picamera2 safely...")
        time.sleep(2)  # Ensure camera is fully available before restarting
        picam2 = Picamera2()  # Reinitialize Picamera2 to avoid issues
        picam2.configure(camera_config)
        picam2.start()

    elif key == 27:  # ESC key (Exit)
        break

# Clean up
cv2.destroyAllWindows()
picam2.stop()
