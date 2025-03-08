from picamera2 import Picamera2
import cv2
import os
from datetime import datetime

# Initialize the camera
picam2 = Picamera2()
camera_config = picam2.create_still_configuration()
picam2.configure(camera_config)

# Ensure the Pictures directory exists
save_dir = "/home/tipqc/Pictures/DATASET/NONFRESH"
os.makedirs(save_dir, exist_ok=True)

# Start the camera
picam2.start_preview()
picam2.start()

# Zoom settings (Using Region of Interest - ROI)
zoom_factor = 1.0  # Default (1.0 = no zoom)
zoom_step = 0.1  # Zoom step
min_zoom = 1.0  # Minimum zoom (full frame)
max_zoom = 3.0  # Maximum zoom (adjustable)
sensor_w, sensor_h = picam2.sensor_resolution  # Get sensor resolution

print("Press SPACEBAR to capture an image, ↑ to zoom in, ↓ to zoom out, ESC to exit.")

def update_zoom():
    """Updates the camera's region of interest (ROI) for zooming."""
    global zoom_factor
    zoom_w = int(sensor_w / zoom_factor)
    zoom_h = int(sensor_h / zoom_factor)
    x1 = (sensor_w - zoom_w) // 2
    y1 = (sensor_h - zoom_h) // 2
    roi = (x1, y1, zoom_w, zoom_h)
    picam2.set_controls({"ScalerCrop": roi})  # Apply zoom

update_zoom()  # Apply initial zoom setting

photo_count = 1  # Counter for multiple captures

while True:
    # Capture a preview frame
    frame = picam2.capture_array()

    # Convert from RGB to BGR for OpenCV display
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # Show the preview
    cv2.imshow("Camera Preview", frame)

    # Wait for key press
    key = cv2.waitKey(1) & 0xFF
    if key == 32:  # Spacebar pressed (Capture Image)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(save_dir, f"captured_image_{timestamp}.jpg")
        picam2.capture_file(filename)
        print(f"Image saved as {filename}")
        photo_count += 1  # Increment photo count

    elif key == 27:  # ESC key (Exit)
        break

    elif key == 82:  # Up arrow key (Zoom In)
        if zoom_factor < max_zoom:
            zoom_factor += zoom_step
            update_zoom()
            print(f"Zoom In: {zoom_factor:.1f}x")

    elif key == 84:  # Down arrow key (Zoom Out)
        if zoom_factor > min_zoom:
            zoom_factor -= zoom_step
            update_zoom()
            print(f"Zoom Out: {zoom_factor:.1f}x")

# Clean up
cv2.destroyAllWindows()
picam2.stop()
