import pyaudio
import struct
from time import sleep
from lcd import lcd_init, initialize_display, update_display_line, scroll_message, value_display, detect, no_detect
from ledbuzzer import setup_gpio, turn_on_buzzer, turn_off_buzzer, control_led, clear_leds
import pvrhino
from sms import send_sms, read_phone_numbers
import RPi.GPIO as GPIO
import time
import time
from buttons import shutdown_on_button_press
import threading
# Path to your Rhino .rhn model
RHINO_MODEL_PATH = "/home/pi/thesis/model/ContructionCode_en_raspberry-pi_v3_0_0.rhn"

# Audio stream parameters
SAMPLE_RATE = 16000  # Rhino requires 16 kHz
FRAME_LENGTH = 512   # Rhino's frame length for processing audio

def type_accident(type_code, accident_code, severity):
    specific_type = "Unknown"
    if type_code == "A":
        # Handle specific accident types based on severity and accident code
        if accident_code == "One":
            if severity == "C":
                specific_type = "Scaffolding Collapse"
            elif severity == "H":
                specific_type = "Slips and Trips"
            elif severity == "M":
                specific_type = "Electric Shock"
            elif severity == "L":
                specific_type = "Minor Cuts and Scrapes"
            
        elif accident_code == "Two":
            if severity == "C":
                specific_type = "Excavation Accidents"
            elif severity == "H":
                specific_type = "Vehicle Rollovers"
            elif severity == "M":
                specific_type = "Slips and Trips"
            elif severity == "L":
                specific_type = "Slips and Trips (Minor)"
            
            
        elif accident_code == "Three":
            if severity == "C":
                specific_type = "Rollover Accidents"
            elif severity == "H":
                specific_type = "Struck-by Vehicles"
                
        elif accident_code == "Four":
            if severity == "C":
                specific_type = "Fire or Explosion"
            elif severity == "H":
                specific_type = "Caught Between Objects"
                
            
        elif accident_code == "Five":
            if severity == "C":
                specific_type = "Vehicle Collisions"
            elif severity == "H":
                specific_type = "Falling Objects"
            
        elif accident_code == "Six":
            if severity == "C":
                specific_type = "Trench Collapses"
               
            
        elif accident_code == "Seven":
            if severity == "C":
                specific_type = "Falls from Heights"
    else:
        event_type = "-"
        specific_type = "-"
    return specific_type

def type_hazard(type_code, accident_code, severity):
    specific_type = "-"
    if type_code == "H":
        if accident_code == "One":
            if severity == "C":
                specific_type = "Electrocution"
            elif severity == "H":
                specific_type = "Noise Pollution"
            elif severity == "M":
                specific_type = "Hearing Loss"
            elif severity == "L":
                specific_type = "Cold Stress"
            
        elif accident_code == "Two":
            if severity == "C":
                specific_type = "Hazardous Materials Exposure"
            elif severity == "H":
                specific_type = "Lifting Hazards"
            elif severity == "M":
                specific_type = "Skin Disorders"
            elif severity == "L":
                specific_type = "Mental Health Issues"
                
            
        elif accident_code == "Three":
            if severity == "C":
                specific_type = "Confined Spaces"
            elif severity == "H":
                specific_type = "Overhead Hazards"
            elif severity == "M":
                specific_type = "Resperitory Issue"
            elif severity == "L":
                specific_type = "Poisoning"
               
            
        elif accident_code == "Four":
            if severity == "H":
                specific_type = "Unstable Structure"
            elif severity == "M":
                specific_type = "Musculoskeletal Disorder"
            elif severity == "L":
                specific_type = "Sleep Disorders"
                    
        elif accident_code == "Five":
            if severity == "H":
                specific_type = "Airborne Dust (Silica Dust)"
            elif severity == "M":
                specific_type = "Fatigue"
                
            
        elif accident_code == "Six":
            if severity == "H":
                specific_type = "Chemical Spill"
            elif severity == "M":
                specific_type = "Inadequete Fall Protection"
      
        elif accident_code == "Seven":
            
            if severity == "M":
                specific_type = "Poor Lighting"
             
                    
        elif accident_code == "Eight":
                
            if severity == "M":
                specific_type = "Lack of Personal Protective Equipment"
                
            
        elif accident_code == "Nine":
           
            if severity == "M":
                specific_type = "Poor Ergonomics"
                
    else:
        event_type = "-"
        specific_type = "-"
    return specific_type


def inference_callback(inference):
    """Callback to process inference and update display."""
    #print('Inferring intent ...\n')
    update_display_line(f"Detecting.....", 0x80)
    if inference.is_understood:
        #print('{')
        #print(f"  intent : '{inference.intent}'")
        #print('  slots : {')
        #for slot, value in inference.slots.items():
           # print(f"    {slot} : '{value}'")
        
        # Extract the relevant slot values for Block, Lot, and Severity
        block = inference.slots.get("BlockNumbers", "-")
        lot = inference.slots.get("LotNumbers", "-")
        
        # Extracting the code values (Critical, Major, Moderate, Low) without the dollar sign
        code_values = [value for key, value in inference.slots.items() if key.lstrip('$') in ["Critical", "High", "Medium", "Low"]]
        code = " ".join(code_values) if code_values else "-"
        
        # Determine Severity based on available slot values (removing dollar sign)
        severity = "-"
        if "Critical" in inference.slots:
            severity = "C"
        elif "High" in inference.slots:
            severity = "H"
        elif "Medium" in inference.slots:
            severity = "M"
        elif "Low" in inference.slots:
            severity = "L"
        
        # Parse the "Code" to detect type (Accident/Hazard) and specific incident
        code_split = code.split()  # e.g., ["C", "A", "One"]
        type_code = code_split[1] if len(code_split) > 1 else ""
        accident_code = code_split[2] if len(code_split) > 2 else ""
        
        # Determine Type and Specific Type
        specific_type = "-"
        if type_code == "A":
            event_type = "Accident"
            specific_type = type_accident(type_code, accident_code, severity)
            control_led(severity, 'accident')
        elif type_code == "H":
            event_type = "Hazard"
            specific_type = type_hazard(type_code, accident_code, severity)
            control_led(severity, 'hazard')
        else:
            event_type = "-"
        
        # Update the display with the parsed values
        value_display(block, lot, severity, code, event_type, specific_type)
          
        # Send SMS with the information
        turn_on_buzzer()
        sleep(1)  # Buzzer stays on for 1 second
        turn_off_buzzer()  # Turn off the buzzer

        # Read phone numbers from the file
        file_path = '/home/pi/thesis/numbers.txt'  # Replace with the actual path to your file
        phone_numbers = read_phone_numbers(file_path)
        
        if phone_numbers:
            sms_message = f"EMERGENCY!! EMERGENCY!! \nBlock: {block}\nLot: {lot}\nCode: {code}\nLevel: {severity}\nType: {event_type}\nDetails: {specific_type}"
            send_sms(phone_numbers, sms_message)
        else:
            print("No phone numbers found to send SMS.")
        
        #print('  }')
        #print('}\n')
    else:
        no_detect()
        time.sleep(1.3)
        detect()
        
        
        #print("Didn't understand the command.\n")

def process_microphone():
    rhino = None
    stream = None
    audio = None
    try:
        # Initialize Rhino
        rhino = pvrhino.create(
            access_key="Fwz4kUT5hgFQIJHmePqQKWq5oQpyOo2IzoDaPdyGnsREnQsgiDu0yA==",
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
        detect()
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
        # Clear LEDs and display values
        print("\nStopping... Turning off LEDs and clearing display values.")
        clear_leds()  # Turn off all LEDs
        
        # Clear display values
        detect()

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
 

   