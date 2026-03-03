import argparse
import os
import subprocess
import sys


def run_dashboard():
    project_root = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(project_root, "src", "dashboard", "app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path], cwd=project_root, check=False)


def run_engine():
    from src.core.audio_engine import run_engine as start_engine

    start_engine()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=["dashboard", "engine"], nargs="?", default="dashboard")
    args = parser.parse_args()
    if args.target == "engine":
        run_engine()
    else:
        run_dashboard()


if __name__ == "__main__":
    main()
