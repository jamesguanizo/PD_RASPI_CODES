import spidev
import time

# Constants
RL = 20.0  # Load resistance in kOhms
VOLTAGE_REF = 5.0  # Reference voltage (in volts)
ADC_RESOLUTION = 1023.0  # ADC resolution (10-bit)
CLEAN_AIR_RS_RO_RATIO_MQ136 = 3.6  # Rs/Ro ratio in clean air for MQ136
CLEAN_AIR_RS_RO_RATIO_MQ137 = 3.7  # Rs/Ro ratio in clean air for MQ137

# SPI setup for MCP3008
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0
spi.max_speed_hz = 1350000

# Function to read from MCP3008
def read_adc(channel):
    if channel < 0 or channel > 7:
        return -1
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    raw_value = ((adc[1] & 3) << 8) + adc[2]
    return raw_value

# Function to calculate Ro
def calculate_ro(channel, rs_ro_ratio):
    analog_sum = 0.0

    # Read the sensor values multiple times to average
    for test_cycle in range(500):  # Take 500 readings
        raw_value = read_adc(channel)
        analog_sum += raw_value
        time.sleep(0.01)  # Small delay between readings

    # Calculate the average analog value
    analog_avg = analog_sum / 500.0

    # Convert analog value to voltage
    vrl = analog_avg * (VOLTAGE_REF / ADC_RESOLUTION)

    # Calculate Rs
    rs = ((VOLTAGE_REF / vrl) - 1) * RL

    # Calculate Ro (Rs / RsRo ratio)
    ro = rs / rs_ro_ratio

    return ro

# Main loop
if __name__ == "__main__":
    try:
        while True:
            # Calculate Ro for MQ136 (connected to channel 0)
            ro_mq136 = calculate_ro(0, CLEAN_AIR_RS_RO_RATIO_MQ136)
            print(f"MQ136 Ro value = {ro_mq136:.2f} kOhms")

            # Calculate Ro for MQ137 (connected to channel 1)
            ro_mq137 = calculate_ro(1, CLEAN_AIR_RS_RO_RATIO_MQ137)
            print(f"MQ137 Ro value = {ro_mq137:.2f} kOhms")

            time.sleep(1)  # Delay of 1 second
    except KeyboardInterrupt:
        print("\nProgram stopped.")
        spi.close()
