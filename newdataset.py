from picamera2 import Picamera2
import cv2
import os
import subprocess
from datetime import datetime
import time

# Ensure the dataset directory exists
save_dir = "/home/tipqc/Pictures/DATASET/FRESH"
os.makedirs(save_dir, exist_ok=True)

# Initialize the camera
picam2 = Picamera2()
camera_config = picam2.create_still_configuration()
picam2.configure(camera_config)
picam2.start()

print("Press SPACEBAR to capture an HDR image with autofocus, ESC to exit.")

while True:
    try:
        # Capture a preview frame
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Camera Preview", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # Spacebar (Capture HDR Image)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(save_dir, f"captured_image_{timestamp}.jpg")

            print("Stopping picamera2 to free the camera...")
            picam2.stop()  # Stop Picamera2 before using libcamera-still
            time.sleep(2)  # Ensure the camera is fully released

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

            print("Restarting picamera2...")
            try:
                picam2 = Picamera2()  # Reinitialize picamera2
                camera_config = picam2.create_still_configuration()
                picam2.configure(camera_config)
                picam2.start()
                print("Picamera2 restarted successfully.")
            except Exception as e:
                print(f"Failed to restart picamera2: {e}")
                break  # Exit loop if camera fails to restart

        elif key == 27:  # ESC key (Exit)
            break

    except Exception as e:
        print(f"Unexpected error: {e}")
        break  # Exit loop on unexpected errors

# Clean up
cv2.destroyAllWindows()
picam2.stop()
