import spidev
import time

# Setup SPI (MCP3008)
spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, device 0 (SPI0)

# MCP3008 channel configuration (assuming both MQ136 and MQ137 are connected to channels 0 and 1)
CHANNEL_MQ136 = 0  # MQ136 connected to channel 0
CHANNEL_MQ137 = 2  # MQ137 connected to channel 1

def read_adc(channel):
    """Read the ADC value from the specified channel (0-7)"""
    if channel > 7 or channel < 0:
        return -1
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    adc_value = ((r[1] & 3) << 8) + r[2]
    return adc_value

def mq_to_ppm(adc_value, sensor_type):
    """
    Convert ADC value to PPM (calibration required for accurate results).
    
    This is a placeholder conversion. Replace it with real calibration data for MQ136 and MQ137.
    """
    if sensor_type == "MQ136":
        # Placeholder calibration for MQ136 (ammonia)
        # Replace with the correct formula and constants based on datasheet or calibration
        ppm = adc_value * 0.1  # Simplified example conversion
    elif sensor_type == "MQ137":
        # Placeholder calibration for MQ137 (ammonia)
        # Replace with the correct formula and constants based on datasheet or calibration
        ppm = adc_value * 0.2  # Simplified example conversion
    else:
        ppm = 0
    return ppm

def main():
    try:
        while True:
            # Read ADC values for MQ136 and MQ137
            adc_mq136 = read_adc(CHANNEL_MQ136)
            adc_mq137 = read_adc(CHANNEL_MQ137)
            
            # Convert ADC to PPM
            ppm_mq136 = mq_to_ppm(adc_mq136, "MQ136")
            ppm_mq137 = mq_to_ppm(adc_mq137, "MQ137")
            
            # Print the PPM values
            print(f"MQ136 (Ammonia) PPM: {ppm_mq136:.2f}")
            print(f"MQ137 (Ammonia) PPM: {ppm_mq137:.2f}")
            
            time.sleep(1)  # Delay before next reading

    except KeyboardInterrupt:
        print("Program terminated")

if __name__ == "__main__":
    main()
