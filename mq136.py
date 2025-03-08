import spidev
import time
import math

# Initialize SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0
spi.max_speed_hz = 1350000

def read_adc(channel):
    """
    Reads data from the specified ADC channel (0-7).
    :param channel: ADC channel number (0-7)
    :return: 10-bit ADC value (0-1023)
    """
    if channel < 0 or channel > 7:
        raise ValueError("ADC channel must be between 0 and 7.")

    # MCP3008 SPI protocol
    command = [1, (8 + channel) << 4, 0]
    response = spi.xfer2(command)
    
    # Combine the response to get the 10-bit result
    adc_value = ((response[1] & 3) << 8) + response[2]
    return adc_value

def calculate_voltage(adc_value, v_ref=3.3):
    """
    Converts ADC value to voltage.
    :param adc_value: ADC value (0-1023)
    :param v_ref: Reference voltage for the ADC
    :return: Voltage corresponding to ADC value
    """
    return (adc_value / 1023.0) * v_ref

def calculate_ppm(voltage):
    """
    Converts voltage to gas concentration in PPM based on the sensor's formula.
    Modify constants based on MQ136 datasheet or calibration data.
    :param voltage: Output voltage from the sensor
    :return: Gas concentration in PPM
    """
    # Constants (a and b) from the sensor calibration curve
    a = 0.05  # Example value, replace with datasheet/calibrated value
    b = -0.85  # Example value, replace with datasheet/calibrated value

    # Avoid negative voltage or undefined PPM
    if voltage <= 0:
        return 0

    ppm = a * (voltage ** b)
    return ppm

def main():
    try:
        while True:
            # Read ADC value from channel 0
            adc_value = read_adc(0)
            
            # Convert ADC value to voltage
            voltage = calculate_voltage(adc_value)
            
            # Calculate PPM
            ppm = calculate_ppm(voltage)
            
            print(f"ADC Value: {adc_value}, Voltage: {voltage:.2f} V, PPM: {ppm:.2f}")
            
            # Add a delay for stability
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        spi.close()

if __name__ == "__main__":
    main()
