import sys
import os

# Ensure the parent directory is in the path to find local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core import moshi_app
from src.core import user_transcriber

def run_engine():
    """
    Starts the Moshi AI Engine with integrated Sentiment Analysis.
    This replaces the old subprocess method with a direct Python call.
    """
    print("🚀 Starting VoxIntel Audio Engine (Powered by Moshi MLX)...")
    
    # --- Start User Transcription (Background Thread) ---
    try:
        print("👂 Starting User Speech Transcription...")
        user_transcriber.start_transcription()
    except Exception as e:
        print(f"⚠️ Warning: Could not start User Transcriber. Make sure PyAudio is installed correctly. Error: {e}")
    # --------------------------------------------------
    
    # We need to set sys.argv manually to simulate command line arguments for moshi_app
    # Default configuration: Quantized 4-bit model
    sys.argv = [
        "moshi_app.py",
        "-q", "4",
        "--hf-repo", "kyutai/moshiko-mlx-q4"
    ]
    
    try:
        moshi_app.main()
    except KeyboardInterrupt:
        print("\n🛑 Audio Engine stopped by user.")
    except Exception as e:
        print(f"\n❌ Error running Audio Engine: {e}")

if __name__ == "__main__":
    run_engine()
