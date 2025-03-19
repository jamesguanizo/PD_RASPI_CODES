from picamera2 import Picamera2
import cv2
import os
import subprocess
from datetime import datetime
import time

save_dir = "/home/tipqc/Pictures/DATASET/FRESH"
os.makedirs(save_dir, exist_ok=True)

def initialize_camera():
    picam2 = Picamera2()
    config = picam2.create_preview_configuration()
    picam2.configure(config)
    picam2.start()
    return picam2

def capture_hdr_image(filename):
    try:
        subprocess.run([
            "libcamera-still",
            "--hdr",
            "--autofocus-mode", "auto",
            "-o", filename
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error capturing HDR image: {e}")
        return False

picam2 = initialize_camera()
print("Press SPACEBAR to capture, ESC to exit")

try:
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Preview", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # Spacebar
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(save_dir, f"captured_image_{timestamp}.jpg")
            
            # Clean up picamera2 resources
            picam2.stop()
            picam2.close()
            
            # Ensure camera release
            time.sleep(1)
            
            # Capture with libcamera-still
            if capture_hdr_image(filename):
                print(f"Captured: {filename}")
            
            # Reinitialize camera
            picam2 = initialize_camera()

        elif key == 27:  # ESC
            break

finally:
    cv2.destroyAllWindows()
    picam2.stop()
    picam2.close()
