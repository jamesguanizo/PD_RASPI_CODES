import cv2
import numpy as np

# Function to initialize the camera
def initialize_camera():
    cap = cv2.VideoCapture(13, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print("Error: Unable to access camera.")
        exit()
    
    cap.set(3, 640)  # Set width
    cap.set(4, 480)  # Set height
    return cap

# Function for template matching
def detect_fish(frame, template):
    # Convert the frame to grayscale
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Perform template matching
    result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8  # Set a threshold for detection

    # Get locations where the match is above the threshold
    loc = np.where(result >= threshold)

    # Draw rectangles around detected matches
    for pt in zip(*loc[::-1]):
        cv2.rectangle(frame, pt, (pt[0] + template.shape[1], pt[1] + template.shape[0]), (0, 255, 0), 2)

    return frame

# Main function
def main():
    # Load the template image (make sure the path is correct)
    template = cv2.imread('/home/tipqc/Downloads/bangus-solo.png', 0)
    if template is None:
        print("Error: Template image not found.")
        exit()

    # Initialize the camera
    cap = initialize_camera()

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: Failed to capture image.")
            break

        # Detect the fish in the captured frame
        detected_frame = detect_fish(frame, template)

        # Display the processed frame
        cv2.imshow("Fish Detector", detected_frame)

        # Break the loop on pressing 'q'
        key = cv2.waitKey(1)
        if key == ord('q'):  # Press 'q' to quit
            break

    # Release the camera and close the window
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
