import spidev
import time
from collections import deque

# Initialize SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0
spi.max_speed_hz = 1350000

# Function to read from MCP3008 with error handling
def read_adc(channel):
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be between 0 and 7")
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    value = ((adc[1] & 3) << 8) + adc[2]
    return value

# Function to calculate PPM for MQ136 (Nitrogen Dioxide)
def calculate_ppm_mq136(raw_value):
    # Constants based on MQ136 datasheet (example values; adjust after calibration)
    RL = 10.0  # Load resistance in kOhms
    RO = 10.0  # Sensor resistance at clean air in kOhms

    if raw_value == 0:
        return 0  # Skip if the raw value is invalid

    # Calculate sensor resistance (RS)
    RS = RL * (1023.0 / raw_value - 1.0)

    # Ratio of RS/RO
    ratio = RS / RO

    # Convert ratio to PPM using a power-law equation
    a = 110.0  # Example coefficient for NO2 sensor
    b = -2.7   # Example exponent for NO2 sensor

    ppm = a * (ratio ** b)
    return ppm

# Moving average function for smoothing
def moving_average(values, window_size=5):
    return sum(values) / len(values)

# Function to scan for the highest values
def scan_highest_values(scan_duration):
    highest_raw_mq137 = 0
    highest_ppm_mq136 = 0

    mq137_values = deque(maxlen=5)  # Store last 5 raw values for smoothing
    mq136_ppm_values = deque(maxlen=5)  # Store last 5 PPM values for smoothing

    start_time = time.time()

    while time.time() - start_time < scan_duration:
        # Read raw value for MQ137 (CH2)
        raw_value_mq137 = read_adc(2)
        mq137_values.append(raw_value_mq137)
        smoothed_raw_mq137 = moving_average(mq137_values)
        if smoothed_raw_mq137 > highest_raw_mq137:
            highest_raw_mq137 = smoothed_raw_mq137

        # Read raw value for MQ136 (CH3)
        raw_value_mq136 = read_adc(3)
        ppm_mq136 = calculate_ppm_mq136(raw_value_mq136)
        mq136_ppm_values.append(ppm_mq136)
        smoothed_ppm_mq136 = moving_average(mq136_ppm_values)
        if smoothed_ppm_mq136 > highest_ppm_mq136:
            highest_ppm_mq136 = smoothed_ppm_mq136

        time.sleep(0.05)  # Reduce delay to increase sampling frequency

    return highest_raw_mq137, highest_ppm_mq136

# Main function
def main():
    user_input = input("Do you want to scan for the highest values? (Y/N): ").strip().upper()
    if user_input == "Y":
        scan_duration = 10  # Duration of the scan in seconds
        print(f"Scanning for {scan_duration} seconds...")

        # Perform scanning
        highest_raw_mq137, highest_ppm_mq136 = scan_highest_values(scan_duration)

        # Print results
        print(f"Highest MQ137 Raw Value: {highest_raw_mq137:.2f}")
        print(f"Highest MQ136 PPM Value: {highest_ppm_mq136:.2f}")
    else:
        print("Exiting without scanning.")

# Run the main function
try:
    main()
except KeyboardInterrupt:
    print("Exiting...")
finally:
    spi.close()
