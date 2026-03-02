import threading
import time
import sys
import os
import numpy as np
import sounddevice as sd
import queue
import whisper
import torch

# Ensure parent directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database import db_manager
from src.analysis import sentiment_analyzer

# Audio config
SAMPLE_RATE = 16000 
CHANNELS = 1
BLOCK_SIZE = 4096

# TWO Queues
raw_audio_queue = queue.Queue()
processing_queue = queue.Queue()

def list_microphones():
    print("\n🔍 Scanning Audio Devices...")
    try:
        default_input = sd.query_devices(kind='input')
        print(f"🎤 Default Input Device: {default_input['name']} (Index: {default_input['index']})")
        return default_input['index']
    except Exception as e:
        print(f"⚠️ Error querying devices: {e}")
        return None

def audio_callback(indata, frames, time, status):
    """Callback for sounddevice to capture audio."""
    if status:
        print(f"⚠️ Audio Status: {status}", file=sys.stderr)
    raw_audio_queue.put(indata.copy())

def capture_thread(device_index):
    """Thread 1: The 'Ear' (Capture)."""
    print(f"👂 [Capture Thread] Started listening on device {device_index}...")
    
    # Process every 4 seconds
    buffer_duration = 4 
    buffer_size = int(SAMPLE_RATE * buffer_duration)
    current_buffer = np.zeros(buffer_size, dtype=np.float32)
    buffer_idx = 0
    
    with sd.InputStream(device=device_index, samplerate=SAMPLE_RATE, channels=CHANNELS, callback=audio_callback):
        while True:
            try:
                chunk = raw_audio_queue.get()
                chunk = chunk.flatten()
                
                # --- VISUAL VU METER ---
                amplitude = np.max(np.abs(chunk))
                if amplitude > 0.01:
                    bars = int(amplitude * 30)
                    sys.stdout.write(f"\r🎤 Input Level: [{'|' * bars:<15}]")
                    sys.stdout.flush()
                # -----------------------

                chunk_len = len(chunk)
                remaining = buffer_size - buffer_idx
                
                if chunk_len >= remaining:
                    current_buffer[buffer_idx:] = chunk[:remaining]
                    
                    # Copy full buffer to processing queue if loud enough
                    if np.max(np.abs(current_buffer)) > 0.02: 
                        processing_queue.put(current_buffer.copy())
                    
                    current_buffer.fill(0)
                    buffer_idx = 0
                    
                    if chunk_len > remaining:
                        leftover = chunk[remaining:]
                        current_buffer[:len(leftover)] = leftover
                        buffer_idx = len(leftover)
                else:
                    current_buffer[buffer_idx:buffer_idx+chunk_len] = chunk
                    buffer_idx += chunk_len
                    
            except Exception as e:
                print(f"\n⚠️ Capture Loop Error: {e}")

def processing_thread():
    """Thread 2: The 'Brain' (Whisper Local)."""
    print("🧠 [Processing Thread] Loading Whisper Base Model (might take a moment)...")
    
    # Load Whisper Model (Small enough for fast CPU/M4 inference)
    try:
        model = whisper.load_model("base.en")
        print("✅ Whisper Model Loaded Successfully!")
    except Exception as e:
        print(f"❌ Failed to load Whisper: {e}")
        return

    while True:
        try:
            # Wait for data
            audio_buffer = processing_queue.get()
            
            # Whisper expects float32 array, which we already have!
            # No need for PCM conversion or temp files.
            
            # Transcribe directly from numpy array
            result = model.transcribe(audio_buffer, fp16=False, language='en')
            text = result['text'].strip()
            
            if text and len(text) > 2: # Ignore empty or tiny noise hallucinations
                print(f"\n✅ Recognized: '{text}'")
                
                # Analyze Sentiment
                score = sentiment_analyzer.get_score(text)
                db_manager.save_entry("User", text, score)
                print(f"💾 Saved Sentiment: {score:.2f}")
            else:
                pass
                # print("\n(Silence/Noise ignored)")
                
        except Exception as e:
            print(f"\n⚠️ Processing Loop Error: {e}")

def start_transcription():
    """Starts both background threads."""
    device_index = list_microphones()
    
    t1 = threading.Thread(target=capture_thread, args=(device_index,), daemon=True)
    t1.start()
    
    t2 = threading.Thread(target=processing_thread, daemon=True)
    t2.start()
    
    return t1, t2

if __name__ == "__main__":
    db_manager.init_db()
    start_transcription()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
