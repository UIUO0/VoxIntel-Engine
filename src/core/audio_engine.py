from src.core import moshi_app, user_transcriber
from src.database import db_manager
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# الكود الأصلي يبدأ من هنا
from src.core import moshi_app, user_transcriber

def run_engine():
    print("🚀 Starting VoxIntel Audio Engine...")
    db_manager.init_db()
    try:
        user_transcriber.start_transcription()
        moshi_app.main(["-q", "4", "--hf-repo", "kyutai/moshiko-mlx-q4"])
    except KeyboardInterrupt:
        print("\n🛑 Audio Engine stopped by user.")
    except Exception as e:
        print(f"\n❌ Error running Audio Engine: {e}")
    finally:
        user_transcriber.stop_transcription()

if __name__ == "__main__":
    run_engine()
