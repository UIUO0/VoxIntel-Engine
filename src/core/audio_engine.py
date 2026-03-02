import subprocess
import sys
import os
import threading
import queue

# Add the src directory to the python path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database import db_manager
from src.analysis import sentiment_analyzer

def run_engine():
    """
    Runs the Moshi AI engine as a subprocess and processes its output in real-time.
    """
    # Ensure database is initialized
    db_manager.init_db()
    
    command = [
        "python", "-m", "moshi_mlx.local",
        "-q", "4",
        "--hf-repo", "kyutai/moshiko-mlx-q4"
    ]
    
    print(f"Starting Audio Engine with command: {' '.join(command)}")
    
    # Start the subprocess
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
        universal_newlines=True
    )
    
    print("Audio Engine started. Listening for output...")

    try:
        # Process stdout line by line
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if not line:
                continue
            
            print(f"[RAW ENGINE OUTPUT]: {line}")
            
            # TODO: Refine parsing logic based on actual Moshi output format.
            # For now, we assume lines starting with specific markers or just treat all non-log lines as text.
            # Adjust this logic once we see the actual output format of moshi_mlx.
            
            speaker = "User"  # Default to User for now, or detect based on line content
            text = line
            
            # Basic filtering to ignore system logs (example)
            if line.startswith("INFO:") or line.startswith("DEBUG:") or line.startswith("Loading"):
                continue
                
            # Analyze sentiment
            score = sentiment_analyzer.get_score(text)
            
            # Save to database
            db_manager.save_entry(speaker, text, score)
            print(f"Saved -> Speaker: {speaker}, Score: {score}, Text: {text[:50]}...")

    except KeyboardInterrupt:
        print("\nStopping Audio Engine...")
    finally:
        process.terminate()
        process.wait()
        print("Audio Engine stopped.")

if __name__ == "__main__":
    run_engine()
