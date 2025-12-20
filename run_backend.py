import sys
import subprocess
import importlib.util
import time
import os

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

def start_server(port: int = 8000):
    print(f"🚀 Starting Video Summarizer Backend on port {port}...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "uvicorn", 
            "video_summarizer.api.main:app", 
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

if __name__ == "__main__":
    # Check for port in args or env
    port = 8000
    if "--port" in sys.argv:
        try:
            port_idx = sys.argv.index("--port")
            port = int(sys.argv[port_idx + 1])
        except (ValueError, IndexError):
            print("⚠️ Invalid port provided, using default 8000")
    elif os.getenv("PORT"):
        try:
            port = int(os.getenv("PORT"))
        except ValueError:
            pass

    # Check if package can be imported
    if not is_installed("video_summarizer"):
        install_package()
    
    start_server(port=port)
