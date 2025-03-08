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

# Function to calculate PPM (calibration needed for accuracy)
def calculate_ppm(raw_value):
    # Constants based on MQ137 datasheet (example values; adjust after calibration)
    RL = 10.0  # Load resistance in kOhms
    RO = 10.0  # Sensor resistance at clean air in kOhms
    CLEAN_AIR_FACTOR = 9.8  # Ratio of RS/RO in clean air

    # Calculate sensor resistance (RS)
    RS = RL * (1023.0 / raw_value - 1.0)

    # Ratio of RS/RO
    ratio = RS / RO

    # Convert ratio to PPM using a power-law equation (example values, replace with calibration curve)
    # PPM = a * (ratio)^b
    a = 116.6020682  # Example coefficient
    b = -2.769034857  # Example exponent

    ppm = a * (ratio ** b)
    return ppm

try:
    while True:
        # Read raw value from CH2 (channel 2)
        raw_value = read_adc(2)

        # Convert to PPM
        ppm = calculate_ppm(raw_value)

        # Print results
        print(f"Raw Value: {raw_value}, PPM: {ppm:.2f}")

        # Delay for readability
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    spi.close()
