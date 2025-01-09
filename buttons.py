import RPi.GPIO as GPIO
import time


def shutdown_on_button_press():
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button 1
    GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button 2


    try:
        while True:
            button_state1 = GPIO.input(16)
            button_state2 = GPIO.input(20)

            if button_state1 == False:  # Button 1 pressed
                print("Button 1 pressed - Shutting down...")
                time.sleep(2)  # Short debounce time
                

            elif button_state2 == False:  # Button 2 pressed
                print("Button 2 pressed")
                time.sleep(0.2)  # Short debounce time

    except KeyboardInterrupt:  # Graceful exit on CTRL+C
        GPIO.cleanup()  # Cleanup GPIO resources
shutdown_on_button_press()
