
import pyaudio
import struct
import pvrhino
import smbus
import RPi.GPIO as GPIO
from time import sleep
import serial
import time

# Path to your Rhino .rhn model
RHINO_MODEL_PATH = "/home/pi/thesis/model/ContructionCode_en_raspberry-pi_v3_0_0.rhn"

# Audio stream parameters
SAMPLE_RATE = 16000  # Rhino requires 16 kHz
FRAME_LENGTH = 512   # Rhino's frame length for processing audio

# I2C Address and Configuration for LCD
I2C_ADDR = 0x27       # LCD I2C address
LCD_WIDTH = 16        # Maximum characters per line (16x4 LCD)
LCD_BACKLIGHT = 0x08  # LCD backlight on
ENABLE = 0b00000100   # Enable bit
E_PULSE = 0.0005
E_DELAY = 0.0005

# LCD Commands
LCD_CMD = 0           # Send command
LCD_CHR = 1           # Send data

DS_PIN = 23  # GPIO4 for DS
SHCP_PIN = 24  # GPIO5 for SHCP
STCP_PIN = 25# GPIO6 for STCP
#NEXT_BUTTON = 17
#PREV_BUTTON = 27
#OK_BUTTON = 22
#RESET_BUTTON = 23
BUZZER_PIN = 18       # Buzzer

# Initialize I2C (bus 1 on most Raspberry Pi models)
bus = smbus.SMBus(1)

# LCD Line Addresses
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0
LCD_LINE_3 = 0x90
LCD_LINE_4 = 0xD0

def lcd_init():
    """Initialize the LCD display."""
    try:
        lcd_byte(0x03, LCD_CMD)
        lcd_byte(0x03, LCD_CMD)
        lcd_byte(0x03, LCD_CMD)
        lcd_byte(0x02, LCD_CMD)

        # LCD initialization sequence
        lcd_byte(0x28, LCD_CMD)  # 4-bit mode, 2 lines, 5x7 dots
        lcd_byte(0x0C, LCD_CMD)  # Display on, cursor off, no blinking
        lcd_byte(0x06, LCD_CMD)  # Increment cursor
        lcd_byte(0x01, LCD_CMD)  # Clear display
        sleep(E_DELAY)
        print("LCD initialized successfully.")
    except Exception as e:
        print(f"Error during LCD initialization: {e}")

def lcd_byte(bits, mode):
    """Send a byte to the LCD."""
    try:
        bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
        bits_low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT

        # Send high bits
        lcd_toggle_enable(bits_high)
        # Send low bits
        lcd_toggle_enable(bits_low)
    except Exception as e:
        print(f"Error in lcd_byte: {e}")

def lcd_toggle_enable(bits):
    """Toggle the enable pin to process data."""
    try:
        bus.write_byte(I2C_ADDR, bits)
        sleep(E_DELAY)
        bus.write_byte(I2C_ADDR, (bits | ENABLE))
        sleep(E_PULSE)
        bus.write_byte(I2C_ADDR, (bits & ~ENABLE))
        sleep(E_DELAY)
    except Exception as e:
        print(f"Error in lcd_toggle_enable: {e}")

def lcd_string(message, line):
    """Send a string to the LCD."""
    try:
        message = message.ljust(LCD_WIDTH, " ")
        lcd_byte(line, LCD_CMD)
        for char in message:
            lcd_byte(ord(char), LCD_CHR)
    except Exception as e:
        print(f"Error in lcd_string: {e}")

# Function to initialize default display
def initialize_display():
    """Initialize the LCD with default messages."""
    lcd_string("Blk: - Lot: -" , LCD_LINE_1)
    lcd_string("Code: -", LCD_LINE_2)
    lcd_string("Level: -", LCD_LINE_3)
    lcd_string("Type: -", LCD_LINE_4)

# Function to update a specific line
def update_display_line(message, line):
    """Update a specific line on the LCD."""
    lcd_string(message, line)
    

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

def setup_gpio():
    """Set up GPIO pins for LEDs and buzzer."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
        
        # Set up shift register control pins as output
    GPIO.setup(DS_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(SHCP_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(STCP_PIN, GPIO.OUT, initial=GPIO.LOW)
        
        # Set up buzzer pin as output
    GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)
        

 

def turn_on_buzzer():
    """Turn on the buzzer."""
    GPIO.output(BUZZER_PIN, GPIO.HIGH)

def turn_off_buzzer():
    """Turn off the buzzer."""
    GPIO.output(BUZZER_PIN, GPIO.LOW)
def inference_callback(inference):
    """Callback to process inference and update display."""

    print('Inferring intent ...\n')
    if inference.is_understood:
        print('{')
        print(f"  intent : '{inference.intent}'")
        print('  slots : {')
        for slot, value in inference.slots.items():
            print(f"    {slot} : '{value}'")
        
        # Extract the relevant slot values for Block, Lot, and Severity
        block = inference.slots.get("BlockNumbers", "-")
        lot = inference.slots.get("LotNumbers", "-")
        
        # Extracting the code values (Critical, Major, Moderate, Low) without the dollar sign
        code_values = [value for key, value in inference.slots.items() if key.lstrip('$') in ["Critical", "High", "Medium", "Low"]]
        code = " ".join(code_values) if code_values else "-"
        
        # Determine Severity based on available slot values (removing dollar sign)
        if "Critical" in inference.slots:
            severity = "Critical"
        elif "High" in inference.slots:
            severity = "High"
        elif "Medium" in inference.slots:
            severity = "Medium"
        elif "Low" in inference.slots:
            severity = "Low"
        
        # Parse the "Code" to detect type (Accident/Hazard) and specific incident
        code_split = code.split()  # e.g., ["C", "A", "One"]
        type_code = code_split[1] if len(code_split) > 1 else ""
        accident_code = code_split[2] if len(code_split) > 2 else ""
        
        # Determine Type based on middle part of the code (Accident or Hazard)
        if type_code == "A":
            event_type = "Accident"
            control_led(severity, 'accident')
            """
            # Handle specific accident types based on severity and accident code
            if accident_code == "One":
                if severity == "Critical":
                    specific_type = "Scaffolding Collapse"
                elif severity == "High":
                    specific_type = "Slips and Trips"
                elif severity == "Medium":
                    specific_type = "Electric Shock"
                elif severity == "Low":
                    specific_type = "Minor Cuts and Scrapes"
                else:
                    specific_type = "Unknown Accident"
            
            elif accident_code == "Two":
                if severity == "Critical":
                    specific_type = "Excavation Accidents"
                elif severity == "High":
                    specific_type = "Vehicle Rollovers"
                elif severity == "Medium":
                    specific_type = "Slips and Trips"
                elif severity == "Low":
                    specific_type = "Slips and Trips (Minor)"
                else:
                    specific_type = "Unknown Accident"
            
            elif accident_code == "Three":
                if severity == "Critical":
                    specific_type = "Rollover Accidents"
                elif severity == "High":
                    specific_type = "Struck-by Vehicles"
                
            
            elif accident_code == "Four":
                if severity == "Critical":
                    specific_type = "Fire or Explosion"
                elif severity == "High":
                    specific_type = "Caught Between Objects"
                
            
            elif accident_code == "Five":
                if severity == "Critical":
                    specific_type = "Vehicle Collisions"
                elif severity == "High":
                    specific_type = "Falling Objects"
            
            elif accident_code == "Six":
                if severity == "Critical":
                    specific_type = "Trench Collapses"
               
            
            elif accident_code == "Seven":
                if severity == "Critical":
                    specific_type = "Falls from Heights"
  """
         
        elif type_code == "H":
            event_type = "Hazard"
            control_led(severity, 'hazard')
            # Handle specific hazard types based on severity and accident code
            """" 
            if accident_code == "One":
                if severity == "Critical":
                    specific_type = "Electrocution"
                elif severity == "High":
                    specific_type = "Noise Pollution"
                elif severity == "Medium":
                    specific_type = "Hearing Loss"
                elif severity == "Low":
                    specific_type = "Cold Stress"
                else:
                    specific_type = "Unknown Hazard"
            
            elif accident_code == "Two":
                if severity == "Critical":
                    specific_type = "Hazardous Materials Exposure"
                elif severity == "High":
                    specific_type = "Lifting Hazards"
                elif severity == "Medium":
                    specific_type = "Skin Disorders"
                elif severity == "Low":
                    specific_type = "Mental Health Issues"
                
            
            elif accident_code == "Three":
                if severity == "Critical":
                    specific_type = "Confined Spaces"
                elif severity == "High":
                    specific_type = "Overhead Hazards"
                elif severity == "Medium":
                    specific_type = "Resperitory Issue"
                elif severity == "Low":
                    specific_type = "Poisoning"
               
            
            elif accident_code == "Four":
                if severity == "High":
                    specific_type = "Unstable Structure"
                elif severity == "Medium":
                    specific_type = "Musculoskeletal Disorder"
                elif severity == "Low":
                    specific_type = "Sleep Disorders"
                
            
            elif accident_code == "Five":
                if severity == "High":
                    specific_type = "Airborne Dust (Silica Dust)"
                elif severity == "Medium":
                    specific_type = "Fatigue"
                
            
            elif accident_code == "Six":
                if severity == "High":
                    specific_type = "Chemical Spill"
                elif severity == "Medium":
                    specific_type = "Inadequete Fall Protection"
      
            elif accident_code == "Seven":
            
                if severity == "Medium":
                    specific_type = "Poor Lighting"
             
                    
            elif accident_code == "Eight":
                
                if severity == "Medium":
                    specific_type = "Lack of Personal Protective Equipment"
                
            
            elif accident_code == "Nine":
           
                if severity == "Medium":
                    specific_type = "Poor Ergonomics"
                """
            
        else:
            event_type = "-"
            #specific_type = "-"
        
        # Update the display with the parsed values
        update_display_line(f"Blk: {block} Lot: {lot}", LCD_LINE_1)
        update_display_line(f"Code: {code}", LCD_LINE_2)
        update_display_line(f"Level: {severity}", LCD_LINE_3)
        update_display_line(f"Type: {event_type}", LCD_LINE_4)
        # Update the sliding text for the 4th line
          
        # Send SMS with the information
        turn_on_buzzer()
        sleep(1)  # Buzzer stays on for 1 second
        turn_off_buzzer()  # Turn off the buzzer

        sms_message = f"EMERGENCY!! EMERGENCY!! \nBlock: {block}\nLot: {lot}\nCode: {code}\nLevel: {severity}\nType: {event_type}"#, {specific_type}
        
        phone_numbers = ['+639944573460']
        send_sms(phone_numbers, sms_message)
        
        print('  }')
        print('}\n')
    else:
        if not inference.is_understood:
            print("Didn't understand the command.\n")
            return

def control_led(severity, event_type):
    """Control the LEDs based on severity and event type."""
    # Prepare the LED state
    leds_state = [0, 0, 0, 0, 0, 0, 0, 0]  # All LEDs off

    if severity == "Critical":
        # Red LEDs (QA, QB) for critical
        if event_type == "accident":
            leds_state[7] = 1  # Red LED 1
        elif event_type == "hazard":
            leds_state[6] = 1  # Red LED 2
    elif severity == "High":
        # Orange LEDs (QC, QD) for major
        if event_type == "accident":
            leds_state[5] = 1  # Orange LED 1
        elif event_type == "hazard":
            leds_state[4] = 1  # Orange LED 2
    elif severity == "Medium":
        # Yellow LEDs (QE, QF) for moderate
        if event_type == "accident":
            leds_state[3] = 1  # Yellow LED 1
        elif event_type == "hazard":
            leds_state[2] = 1  # Yellow LED 2
    elif severity == "Low":
        # Green LEDs (QG, QH) for low
        if event_type == "accident":
            leds_state[1] = 1  # Green LED 1
        elif event_type == "hazard":
            leds_state[0] = 1  # Green LED 2

    # Light the appropriate LED based on event type (Accident or Hazard)
    if event_type == "accident":
        # Light accident-related LEDs (red for critical)
        shift_out(leds_state)
    elif event_type == "hazard":
        # Light hazard-related LEDs (orange for hazard)
        shift_out(leds_state)
    print( event_type, leds_state)
    
def shift_out(leds_state):
    """Shift out the LED state to the shift register."""
    GPIO.output(DS_PIN, 0)  # Start low
    for bit in leds_state:
        GPIO.output(SHCP_PIN, 0)  # Clock low
        GPIO.output(DS_PIN, bit)  # Send data bit
        GPIO.output(SHCP_PIN, 1)  # Clock high
        GPIO.output(SHCP_PIN, 0)  # Clock low
    GPIO.output(STCP_PIN, 1)  # Latch the data to the output
    GPIO.output(STCP_PIN, 0)  # Clear the latch

def process_microphone():
    rhino = None
    stream = None
    audio = None
    try:
        # Initialize Rhino
        rhino = pvrhino.create(
            access_key="Fwz4kUT5hgFQIJHmePqQKWq5oQpyOo2IzoDaPdyGnsREnQsgiDu0yA==",  # Replace with your Picovoice access key
            context_path=RHINO_MODEL_PATH,
        )
        
        # Initialize Audio Stream
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=FRAME_LENGTH,
        )

        # Initialize LCD and GPIO
        lcd_init()
        initialize_display()
        setup_gpio()
        turn_off_buzzer()
        
        print("GPIO setup complete. All LEDs and buzzer should be off.")
        print("Listening... (Press Ctrl+C to stop)")

        while True:
            frame = stream.read(FRAME_LENGTH, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * FRAME_LENGTH, frame)
            is_finalized = rhino.process(pcm)

            if is_finalized:
                inference = rhino.get_inference()
                inference_callback(inference)  # Call the callback for inference results

    except KeyboardInterrupt:
        
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Safely close resources if they were opened
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if audio is not None:
            audio.terminate()
        if rhino is not None:
            rhino.delete()
        GPIO.cleanup()  # Clean up GPIO settings



if __name__ == "__main__":
    process_microphone()
   
