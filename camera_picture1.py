import time
import subprocess
import keyboard  # Install with 'pip install keyboard' if not available

def capture_high_quality_image(output_dir="/home/pi/Pictures/"):
    filename = f"{output_dir}image_{time.strftime('%Y%m%d-%H%M%S')}.jpg"
    
    command = [
        "libcamera-still",
        "-o", filename,
        "--width", "3280",
        "--height", "2464",
        "--quality", "100",
        "--denoise", "cdn_off"
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Image saved: {filename}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Press SPACEBAR to capture an image...")
    while True:
        if keyboard.is_pressed("space"):
            print("Capturing image...")
            capture_high_quality_image()
            time.sleep(1)  # Prevent accidental multiple captures
