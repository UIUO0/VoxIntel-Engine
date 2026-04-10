import sys
import time
import sounddevice as sd
import numpy as np

def test_microphone():
    print("🎤 Streaming from microphone...")
    print("If you do not see a macOS microphone permission prompt (or if it crashes),")
    print("your Python environment might lack microphone access.")
    print("-" * 50)
    
    try:
        def audio_callback(indata, frames, time_info, status):
            if status:
                print(status)
            volume_norm = np.linalg.norm(indata) * 10
            # Print a simple volume meter
            print("|" * int(volume_norm))

        # Open a minimal audio stream for 5 seconds
        stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=16000)
        with stream:
            print("Listening for 5 seconds... Please speak into the mic.")
            time.sleep(5)
            
        print("-" * 50)
        print("✅ Microphone test completed successfully!")
    except Exception as e:
        print(f"❌ Audio Test Failed!\nError details: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_microphone()
