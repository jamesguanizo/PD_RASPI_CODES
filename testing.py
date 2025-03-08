import spidev
import time

# Initialize SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0
spi.max_speed_hz = 1350000

# Function to read from MCP3008
def read_adc(channel):
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be between 0 and 7")
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    value = ((adc[1] & 3) << 8) + adc[2]
    return value

# Function to calculate PPM for MQ137 (Ammonia)
def calculate_ppm_mq137(raw_value):
    # Constants based on MQ137 datasheet (example values; adjust after calibration)
    RL = 8.0  # Load resistance in kOhms
    RO = 8.0  # Sensor resistance at clean air in kOhms

    # Calculate sensor resistance (RS)
    RS = RL * (1023.0 / raw_value - 1.0)

    # Ratio of RS/RO
    ratio = RS / RO

    # Convert ratio to PPM using a power-law equation (example values, replace with calibration curve)
    a = 116.6020682  # Example coefficient
    b = -2.769034857  # Example exponent

    ppm = a * (ratio ** b)
    return ppm

# Function to calculate PPM for MQ136 (Nitrogen Dioxide)
def calculate_ppm_mq136(raw_value):
    # Constants based on MQ136 datasheet (example values; adjust after calibration)
    RL = 8.0  # Loaresistance in kOhms
    RO = 8.0  # Sensor resistance at clean air in kOhms

    # Calculate sensor resistance (RS)
    RS = RL * (1100.0 / raw_value - 1.0)

    # Ratio of RS/RO
    ratio = RS / RO

    # Convert ratio to PPM using a power-law equation (example values, replace with calibration curve)
    a = 110.0  # Example coefficient for NO2 sensor
    b = -2.7    # Example exponent for NO2 sensor

    ppm = a * (ratio ** b)
    return ppm

try:
    while True:
        # Read raw value from CH2 (channel 2) for MQ137
        raw_value_mq137 = read_adc(2)

        # Read raw value from CH3 (channel 3) for MQ136
        raw_value_mq136 = read_adc(0)

        # Convert to PPM
        ppm_mq137 = calculate_ppm_mq137(raw_value_mq137)
        ppm_mq136 = calculate_ppm_mq136(raw_value_mq136)

        # Print results
        print(f"MQ137 Raw Value: {raw_value_mq137}, PPM: {ppm_mq137:.2f}")
        print(f"MQ136 Raw Value: {raw_value_mq136}, PPM: {ppm_mq136:.2f}")

        # Delay for readability
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    spi.close()
