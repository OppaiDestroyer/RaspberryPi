import RPi.GPIO as GPIO
import smbus
import time
import os
import serial
from time import sleep
from lcd import lcd_init, lcd_string
import subprocess
import threading


# Define GPIO pins
DS_PIN = 23   # GPIO23 for DS
SHCP_PIN = 24 # GPIO24 for SHCP
STCP_PIN = 25 # GPIO25 for STCP

# Function to check if SIM800L is connected
def check_sim800l_connection():
    try:
        # Replace this with your actual SIM800L check code
        # For example, checking if the modem responds with "OK" to an AT command
        return True  # Simulating a successful connection
    except Exception as e:
        print(f"Error checking SIM800L: {e}")
        return False

# Function to display startup messages
def display_startup_messages():
    # Show "Powering on..."
    lcd_string("Powering on...", 0xC0)
    time.sleep(2)  # Show the message for 2 seconds

    # Check if SIM800L is connected
    sim_status = check_sim800l_connection()
    if sim_status:
        # Show "Sim800L connected"
        lcd_string("Sim800L", 0xC0)
        lcd_string("connected", 0x90)
        time.sleep(2)  # Show the message for 2 seconds
    else:
        # Show error if SIM800L is not connected
        lcd_string("Sim800L Error!",  0xC0)
        time.sleep(2)
        lcd_string("Check Connection", 0x90)
        time.sleep(2)
        return  # Exit if SIM800L isn't connected

    # Show "Ready to use"
    lcd_string("Ready to use",  0xC0)
    lcd_string("", 0x90)
    time.sleep(2)

# GPIO setup function
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DS_PIN, GPIO.OUT)
    GPIO.setup(SHCP_PIN, GPIO.OUT)
    GPIO.setup(STCP_PIN, GPIO.OUT)

    # Ensure all pins are LOW initially
    GPIO.output(DS_PIN, GPIO.LOW)
    GPIO.output(SHCP_PIN, GPIO.LOW)
    GPIO.output(STCP_PIN, GPIO.LOW)
    print("GPIO setup completed.")

# Function to handle the shutdown button press
def shutdown_on_button_press():
    GPIO.setmode(GPIO.BCM)

    # Set up the buttons with pull-up resistors
    GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button 1
    GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button 2

    # Initialize the LCD
    lcd_init()

    try:
        while True:
            button_state1 = GPIO.input(16)
            button_state2 = GPIO.input(20)

            if button_state1 == False:  # Button 1 pressed
                print("Button 1 pressed - Shutting down...")
                
                # Display "Shutting down..." on the LCD screen
                lcd_string("Shutting down...", 0xC0)  # Specify the LCD address
                time.sleep(2)  # Give a short delay to display the message
                
                # Execute shutdown command
                os.system("sudo shutdown now")  # This will shut down the Raspberry Pi
                time.sleep(2)  # Small delay to ensure the shutdown command is executed
                
                break  # Exit the loop after initiating the shutdown

            elif button_state2 == False:  # Button 2 pressed
                print("Button 2 pressed")
                time.sleep(0.2)  # Short debounce time for Button 2

            time.sleep(0.1)  # Poll the buttons every 100 ms

    except KeyboardInterrupt:  # Graceful exit on CTRL+C
        print("Keyboard interrupt detected. Exiting...")
        GPIO.cleanup()  # Cleanup GPIO resources

# Function to run the main script (e.g., running your main application logic)
def run_main_script():
    try:
        venv_path = "/home/pi/thesis/venv/bin/activate"
        script_path = "/home/pi/thesis/main.py"
        command = f"bash -i -c 'source {venv_path} && python3 {script_path}'"
        
        print("Running main.py in virtual environment...")
        subprocess.call(command, shell=True)
    except Exception as e:
        print(f"Error running main.py: {e}")

# Main boot-up sequence
def main():
    setup_gpio()
    lcd_init()
    display_startup_messages()

    try:
        # Start the shutdown button handler in a separate thread
        shutdown_thread = threading.Thread(target=shutdown_on_button_press)
        shutdown_thread.daemon = True  # Daemonize the thread to ensure it closes when the main program exits
        shutdown_thread.start()

        # Run the main script or any other necessary actions in the main thread
        run_main_script()

    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")
        GPIO.cleanup()  # Cleanup GPIO resources

    finally:
        print("Cleanup completed. Program exited.")

if __name__ == "__main__":
    main()
