from picamera2 import Picamera2
import cv2
import numpy as np
from inference_sdk import InferenceHTTPClient

# Initialize the Camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

# Initialize Roboflow Client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="Wk1p4Yv2hc8lK7Of48ME"
)

def draw_boxes(frame, predictions):
    """Draws bounding boxes on the frame based on the detection results."""
    fish_detected = False  # Flag to track detection status
    
    for pred in predictions.get("predictions", []):
        x, y, w, h = int(pred["x"]), int(pred["y"]), int(pred["width"]), int(pred["height"])
        label = f"{pred['class']} ({pred['confidence']:.2f})"
        fish_detected = True  # Fish detected

        # Draw bounding box
        cv2.rectangle(frame, (x - w // 2, y - h // 2), (x + w // 2, y + h // 2), (0, 255, 0), 2)

        # Draw label
        cv2.putText(frame, label, (x - w // 2, y - h // 2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Draw "No Fish Detected" or "Fish Detected" in the upper right corner
    if fish_detected:
        status_text = "Fish Detected"
        color = (0, 255, 0)  # Green
    else:
        status_text = "No Fish Detected"
        color = (0, 0, 255)  # Red

    cv2.putText(frame, status_text, (400, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    return frame

while True:
    frame = picam2.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for OpenCV

    # Save temporary frame for API processing
    temp_image_path = "temp_frame.jpg"
    cv2.imwrite(temp_image_path, frame)

    # Perform object detection
    result = CLIENT.infer(temp_image_path, model_id="fish_detection-z6be1/1")

    # Draw bounding boxes and indicator
    frame = draw_boxes(frame, result)

    # Display the frame with detections
    cv2.imshow("Live Fish Detection", frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cv2.destroyAllWindows()
picam2.close()
