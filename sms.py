import serial
import time

def read_phone_numbers(file_path):
    """
    Reads phone numbers from a text file and returns them as a list.

    :param file_path: Path to the text file containing phone numbers.
    :return: List of phone numbers.
    """
    try:
        with open(file_path, 'r') as file:
            # Read each line and strip any leading/trailing whitespace characters
            phone_numbers = [line.strip() for line in file.readlines()]
        return phone_numbers
    except Exception as e:
        print(f"Error reading phone numbers: {e}")
        return []

def send_sms(phone_numbers, message):
    """
    Send SMS using SIM800L to multiple phone numbers.

    :param phone_numbers: List of phone numbers to send the SMS to.
    :param message: The message to send.
    """
    try:
        sim800l = serial.Serial(
            port='/dev/ttyS0',  # Use appropriate UART port for Raspberry Pi
            baudrate=9600,
            timeout=1
        )

        time.sleep(2)  # Allow SIM800L to initialize

        # Test communication with SIM800L
        sim800l.write(b'AT\r\n')
        response = sim800l.read(64).decode()
        print(f"AT Response: {response.strip()}")

        if 'OK' not in response:
            raise Exception("SIM800L not responding correctly. Check connections.")

        # Set SMS to text mode
        sim800l.write(b'AT+CMGF=1\r\n')
        time.sleep(0.5)
        sim800l.read(64)  # Clear buffer

        # Send SMS to each phone number
        for phone_number in phone_numbers:
            print(f"Sending SMS to {phone_number}...")
            sim800l.write(f'AT+CMGS="{phone_number}"\r'.encode())
            time.sleep(0.5)
            sim800l.write(f'{message}\x1A'.encode())  # End message with Ctrl+Z
            time.sleep(3)  # Allow time for the message to be sent
            print(f"SMS sent to {phone_number}!")

    except Exception as e:
        print(f"Error sending SMS: {e}")
    finally:
        sim800l.close()
