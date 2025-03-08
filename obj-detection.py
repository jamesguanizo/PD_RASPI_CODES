from inference_sdk import InferenceHTTPClient
import cv2
import time
import os

# Initialize Roboflow inference client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="Wk1p4Yv2hc8lK7Of48ME"
)

# Define fish detection models
fish_models = {
    "Milkfish": "chanos-chanos-pnau1/6",
    "Lapu-Lapu": "plectropomus-leopardus-n75jy/1",
    "Tilapia": "tilapia-t0huo/1"
}

def detect_fish(image_path):
    detected_fish = []
    
    for fish_name, model_id in fish_models.items():
        result = CLIENT.infer(image_path, model_id=model_id)
        print(f"API Response for {fish_name}:", result)  # Debugging output

        if result["predictions"]:
            detected_fish.append(fish_name)
    
    return detected_fish

def main():
    cap = cv2.VideoCapture(2)
    cap.set(3, 640)  # Set width
    cap.set(4, 480)  # Set height
    
    if not cap.isOpened():
        print("Error: Camera not found!")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break
        
        image_path = "temp.jpg"
        cv2.imwrite(image_path, frame)  # Save the image
        
        # Ensure the image is saved properly before processing
        if not os.path.exists(image_path):
            print("Error: Image not saved properly.")
            continue
        
        detected_fish = detect_fish(image_path)
        label = ", ".join(detected_fish) if detected_fish else "No fish detected"
        
        cv2.putText(frame, label, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Fish Detection", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.5)  # Slight delay to prevent excessive API calls
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
