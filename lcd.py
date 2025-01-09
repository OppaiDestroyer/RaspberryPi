import smbus
from time import sleep

# I2C Address and Configuration for LCD
I2C_ADDR = 0x27       # LCD I2C address
LCD_WIDTH = 16        # Maximum characters per line (16x4 LCD)
LCD_BACKLIGHT = 0x08  # LCD backlight on
ENABLE = 0b00000100   # Enable bit
E_PULSE = 0.0005
E_DELAY = 0.0005
# LCD Line Addresses
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0
LCD_LINE_3 = 0x90
LCD_LINE_4 = 0xD0
# LCD Commands
LCD_CMD = 0           # Send command
LCD_CHR = 1           # Send data
# Initialize I2C (bus 1 on most Raspberry Pi models)
bus = smbus.SMBus(1)
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
    lcd_string("B: - L: - S: -" , LCD_LINE_1)
    lcd_string("C: -", LCD_LINE_2)
    lcd_string("T: -", LCD_LINE_3)
    lcd_string("D: -", LCD_LINE_4)
def value_display(block, lot, severity, code, event_type, specific_type):
    update_display_line(f"B: {block} L: {lot} S: {severity}", LCD_LINE_1 )
    update_display_line(f"C: {code}", LCD_LINE_2)
    update_display_line(f"T: {event_type}", LCD_LINE_3)
    update_display_line(f"D: {specific_type}", LCD_LINE_4)

def detect():
    update_display_line(f"Listening.....", 0x80)
    update_display_line(f" ", 0xC0)
    update_display_line(f"Detecting.....", 0x90)
    update_display_line(f" ", 0xD0)

def no_detect():
    update_display_line(f"Voice Detected", 0x80)
    update_display_line(f"But did not", 0xC0)
    update_display_line(f"understand", 0x90)
    update_display_line(f"the command!", 0xD0)
# Function to update a specific line
def update_display_line(message, line):
    """Update a specific line on the LCD."""
    lcd_string(message, line)

def scroll_message(message, line, delay=0.3):
    """
    Scroll a message off the display, then restart from the beginning.
    """

    if len(message) <= LCD_WIDTH:
        # If the message fits within the LCD width, just display it
        lcd_string(message.ljust(LCD_WIDTH, " "), line)
        return

    # Add spaces to allow the message to scroll out and reappear
    message = message + " " * LCD_WIDTH

    while True:  # Continuous loop
        for i in range(len(message)):
            lcd_string(message[i:i + LCD_WIDTH], line)
            sleep(delay)

