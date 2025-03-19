from picamera2 import Picamera2
import cv2
import os
import subprocess
from datetime import datetime

# Ensure the Pictures directory exists
save_dir = "/home/tipqc/Pictures/DATASET/NONFRESH"
os.makedirs(save_dir, exist_ok=True)

# Initialize the camera
picam2 = Picamera2()
camera_config = picam2.create_still_configuration()
picam2.configure(camera_config)

# Enable Auto-Focus (AF) Mode
try:
    picam2.set_controls({"AfMode": 2})  # Set to continuous autofocus
except RuntimeError as e:
    print(f"Warning: Auto-focus mode not supported: {e}")

# Start the camera
picam2.start_preview()
picam2.start()

print("Press SPACEBAR to capture an HDR image, ESC to exit.")

while True:
    # Capture a preview frame
    frame = picam2.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imshow("Camera Preview", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == 32:  # Spacebar (Capture HDR Image)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(save_dir, f"captured_image_{timestamp}.jpg")

        print("Triggering autofocus...")
        try:
            picam2.set_controls({"AfTrigger": 1})  # Trigger single autofocus
        except RuntimeError as e:
            print(f"Auto-focus trigger failed: {e}")

        print(f"Capturing HDR image: {filename}")
        subprocess.run(["libcamera-still", "--hdr", "1", "--autofocus", "-o", filename])

        print(f"Image saved as {filename}")

    elif key == 27:  # ESC key (Exit)
        break

# Clean up
cv2.destroyAllWindows()
picam2.stop()
