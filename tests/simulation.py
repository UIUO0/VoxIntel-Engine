import time
import random
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import db_manager

# Sample phrases with approximate sentiment
samples = [
    ("User", "I am very frustrated with your service!", -0.8),
    ("AI", "I apologize for the inconvenience. How can I help?", 0.2),
    ("User", "This is taking too long, I'm angry.", -0.6),
    ("AI", "I am checking your details now, please wait.", 0.1),
    ("User", "Okay, thank you for helping me.", 0.4),
    ("AI", "You are welcome! I found the issue.", 0.6),
    ("User", "Great! That makes me happy.", 0.8),
    ("AI", "Is there anything else?", 0.0),
    ("User", "No, that's it. Have a good day.", 0.5),
    ("User", "Wait, it's broken again! Terrible!", -0.9)
]

def run_simulation():
    print("🚀 Starting Data Simulation...")
    print("Press Ctrl+C to stop.")
    
    db_manager.init_db()
    
    try:
        while True:
            # Pick a random sample
            speaker, text, base_score = random.choice(samples)
            
            # Add some random variation to score
            final_score = max(-1.0, min(1.0, base_score + random.uniform(-0.1, 0.1)))
            
            # Save to DB
            db_manager.save_entry(speaker, text, final_score)
            
            print(f"📝 Inserted: [{speaker}] {text} (Score: {final_score:.2f})")
            
            # Wait a bit to simulate conversation flow
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped.")

if __name__ == "__main__":
    run_simulation()
