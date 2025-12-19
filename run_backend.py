import sys
import subprocess
import importlib.util
import time

def is_installed(package_name):
    try:
        return importlib.util.find_spec(package_name) is not None
    except ImportError:
        return False

def install_package():
    print("📦 Installing video_summarizer package in editable mode...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
        print("✅ Installation successful!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        sys.exit(1)

def start_server():
    print("🚀 Starting Video Summarizer Backend...")
    try:
        # We replace the current process with uvicorn so it handles signals/reload correctly
        # But subprocess.run/call is safer for cross-platform wrapper usually.
        # Since uvicorn --reload spawns subprocesses, using check_call is fine, 
        # but KeyboardInterrupt needs handling.
        subprocess.check_call([sys.executable, "-m", "uvicorn", "video_summarizer.api.main:app", "--reload"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except subprocess.CalledProcessError as e:
        # uvicorn exits with non-zero if it crashes
        sys.exit(e.returncode)

if __name__ == "__main__":
    # Check if package can be imported
    if not is_installed("video_summarizer"):
        install_package()
    else:
        # Optional: Check if we are in an environment where src is not in path but package is installed
        pass

    start_server()
