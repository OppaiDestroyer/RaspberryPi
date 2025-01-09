# voice_to_intent.py
import pyaudio
import struct
import pvrhino

# Path to your Rhino `.rhn` model
RHINO_MODEL_PATH = "/home/pi/thesis/model/ContructionCode_en_raspberry-pi_v3_0_0.rhn"

# Audio stream parameters
SAMPLE_RATE = 16000  # Rhino requires 16 kHz
FRAME_LENGTH = 512   # Rhino's frame length for processing audio

def inference_callback(inference):
    """Callback to process inference and update display."""
    print('Inferring intent ...\n')
    if inference.is_understood:
        print('{')
        print(f"  intent : '{inference.intent}'")
        print('  slots : {')
        for slot, value in inference.slots.items():
            print(f"    {slot} : '{value}'")
        print('  }')
        print('}\n')
    else:
        print("Didn't understand the command.\n")

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
