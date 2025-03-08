import spidev
import time
import math

# Constants
RL_MQ136 = 20.0  # Load resistance in kOhms for MQ136
RO_MQ136 = 40.0  # Sensor resistance in clean air for MQ136
A_MQ136 = 110.0  # Calibration constant for MQ136
B_MQ136 = -2.7  # Exponent for MQ136

RL_MQ137 = 20.0  # Load resistance in kOhms for MQ137
RO_MQ137 = 200.0  # Sensor resistance in clean air for MQ137
A_MQ137 = 116.6020682  # Calibration constant for MQ137
B_MQ137 = -2.769034857  # Exponent for MQ137

ADC_RESOLUTION = 1023.0  # ADC resolution (10-bit)
VOLTAGE_REF = 5.0  # Reference voltage for MCP3008

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

# Function to calculate PPM using calibration constants
def calculate_ppm(raw_value, RL, RO, A, B):
    if raw_value <= 0:  # Prevent division by zero or invalid input
        return 0
    RS = RL * (ADC_RESOLUTION / raw_value - 1.0)  # Calculate sensor resistance
    ratio = RS / RO  # Calculate RS/RO ratio
    ppm = A * math.pow(ratio, B)  # Calculate PPM using the power-law equation
    return ppm

# Main Loop
try:
    while True:
        # Read raw values from MCP3008 channels
        raw_value_mq137 = read_adc(2)  # Assuming MQ137 is connected to channel 2
        raw_value_mq136 = read_adc(0)  # Assuming MQ136 is connected to channel 0

        # Calculate PPM for MQ137
        ppm_mq137 = calculate_ppm(raw_value_mq137, RL_MQ137, RO_MQ137, A_MQ137, B_MQ137)
        print(f"Ammonia Raw Value: {raw_value_mq137}, PPM: {ppm_mq137:.2f}")

        # Calculate PPM for MQ136
        ppm_mq136 = calculate_ppm(raw_value_mq136, RL_MQ136, RO_MQ136, A_MQ136, B_MQ136)
        print(f"Hydrogen Sulfide Raw Value: {raw_value_mq136}, PPM: {ppm_mq136:.2f}")

        # Delay for readability
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting program...")

finally:
    spi.close()
