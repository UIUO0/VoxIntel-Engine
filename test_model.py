import sys
import logging
import traceback

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_model")

def main():
    logger.info("Starting standalone backend isolation test for Moshi...")
    try:
        # Import the model modules
        logger.info("Importing src.core.moshi_app...")
        from src.core import moshi_app

        logger.info("Initializing Moshi model (kyutai/moshiko-mlx-q4)...")
        # Run moshi entrypoint directly
        # If it crashes here, the exception will be caught and printed
        moshi_app.main(["-q", "4", "--hf-repo", "kyutai/moshiko-mlx-q4"])
        logger.info("Moshi main loop completed successfully.")

    except ImportError as ie:
        logger.error(f"IMPORT ERROR: Could not import necessary modules. Check PYTHONPATH and venv.\n{traceback.format_exc()}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"RUNTIME FAILURE: An error occurred during execution:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
