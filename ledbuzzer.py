import RPi.GPIO as GPIO
import time

DS_PIN = 23  # GPIO4 for DS
SHCP_PIN = 24  # GPIO5 for SHCP
STCP_PIN = 25  # GPIO6 for STCP
BUZZER_PIN = 18       # Buzzer

def setup_gpio():
   
    #GPIO pins
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    #shift register control pins as output
    GPIO.setup(DS_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(SHCP_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(STCP_PIN, GPIO.OUT, initial=GPIO.LOW)

    #buzzer pin as output
    GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)

def turn_on_buzzer():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)

def turn_off_buzzer():
 
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def control_led(severity, event_type):
    """Control the LEDs based on severity and event type."""
    # DS PIN
    leds_state = [0, 0, 0, 0, 0, 0, 0, 0]  

    if severity == "C":
        # Red LEDs (QA, QB) for critical
        if event_type == "accident":
      
            leds_state[7] = 1  
        elif event_type == "hazard":
           
            leds_state[6] = 1  
    elif severity == "H":
        # Orange LEDs (QC, QD) for High
        if event_type == "accident":
     
            leds_state[5] = 1 
        elif event_type == "hazard":
           
            leds_state[4] = 1  
    elif severity == "M":
        # Yellow LEDs (QE, QF) for medium
        if event_type == "accident":
         
            leds_state[3] = 1  
        elif event_type == "hazard":
  
            leds_state[2] = 1 
    elif severity == "L":
        # Green LEDs (QG, QH) for low
        if event_type == "accident":
           
            leds_state[1] = 1 
        elif event_type == "hazard":
 
            leds_state[0] = 1  

    # Light the appropriate LED based on event type (Accident or Hazard)
    shift_out(leds_state)

def shift_out(leds_state):
    """Shift out the LED state to the shift register."""
    GPIO.output(DS_PIN, GPIO.LOW)  # Start low
    time.sleep(0.001)  # Optional small delay to ensure timing
    for bit in leds_state:
        GPIO.output(SHCP_PIN, GPIO.LOW)  # Clock low
        GPIO.output(DS_PIN, bit)  # Send data bit
        time.sleep(0.001)  # Optional small delay between bit shifts
        GPIO.output(SHCP_PIN, GPIO.HIGH)  # Clock high
        time.sleep(0.001)  # Optional small delay
        GPIO.output(SHCP_PIN, GPIO.LOW)  # Clock low
    GPIO.output(STCP_PIN, GPIO.HIGH)  # Latch the data to the output
    time.sleep(0.001)  # Optional small delay for stable latch
    GPIO.output(STCP_PIN, GPIO.LOW)  # Clear the latch
       
def clear_leds():
    """Clear all LEDs by setting their state to 0."""
    leds_state = [0, 0, 0, 0, 0, 0, 0, 0]  # All LEDs off
    shift_out(leds_state)  # Shift out the cleared state
