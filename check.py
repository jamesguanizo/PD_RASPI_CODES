from inference_sdk import InferenceHTTPClient
import cv2
import os
import time
import subprocess
import numpy as np

# Initialize Roboflow Inference Client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="Wk1p4Yv2hc8lK7Of48ME"
)

def start_video_stream():
    """Starts libcamera-vid and pipes it to MJPEG stream."""
    cmd = [
        "libcamera-vid", 
        "--width", "640", 
        "--height", "480", 
        "--nopreview",
        "-t", "0",  # Continuous streaming
        "--codec", "mjpeg",
        "-o", "-"
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)

def detect_fish(image_path):
    """Send an image to the inference API and detect fish."""
    try:
        result = CLIENT.infer(image_path, model_id="fish_data-ndafw/2")
        print("API Response:", result)

        return bool(result["predictions"])
    except Exception as e:
        print(f"? Error in API request: {e}")
        return False

def main():
    """Captures video stream and detects fish in real-time."""
    print("? Starting video stream... Press 'q' to exit.")

    # Start the libcamera-vid stream
    process = start_video_stream()

    # Read MJPEG frames directly from libcamera-vid
    frame_width, frame_height = 640, 480
    while True:
        jpeg_data = bytearray()
        while True:
            chunk = process.stdout.read(1024)  # Read small chunks to assemble JPEG
            if not chunk:
                print("? Error: No data received from stream.")
                break
            jpeg_data.extend(chunk)
            if jpeg_data[-2:] == b'\xff\xd9':  # JPEG end marker
                break
        
        # Convert to numpy array and decode
        frame_array = np.asarray(jpeg_data, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

        if frame is None:
            print("? Error: Invalid frame data.")
            continue

        # Save frame for inference
        image_path = "temp.jpg"
        cv2.imwrite(image_path, frame)

        # Detect fish in the frame
        fish_detected = detect_fish(image_path)
        label = "Fish Detected" if fish_detected else "No Fish Detected"

        # Overlay detection result
        color = (0, 255, 0) if fish_detected else (0, 0, 255)
        cv2.putText(frame, label, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.imshow("Fish Detection", frame)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.5)  # Prevent excessive API calls

    # Cleanup
    process.terminate()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
