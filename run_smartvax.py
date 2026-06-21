import os
import sys
import subprocess
import time
import socket

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def run():
    print("="*60)
    print("           SmartVax Application Runner")
    print("="*60)
    
    # 1. Check Python and dependencies
    print("\n[1/3] Checking environment...")
    try:
        import flask
        import sklearn
        import pandas
        print("      OK: Dependencies found.")
    except ImportError:
        print("      INFO: Missing libraries. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # 2. Kill existing process on port 5000
    print("\n[2/3] Cleaning up port 5000...")
    if os.name == 'nt': # Windows
        try:
            output = subprocess.check_output('netstat -aon | findstr :5000', shell=True).decode()
            for line in output.splitlines():
                if ':5000' in line:
                    pid = line.strip().split()[-1]
                    print(f"      Stopping old process (PID {pid})...")
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("      Port 5000 is already free.")

    # 3. Start the server
    print("\n[3/3] Starting SmartVax Server...")
    # Open app.py in a separate process that stays open
    cmd = [sys.executable, "app.py"]
    if os.name == 'nt':
        # On Windows, start in a new command window
        process = subprocess.Popen(["start", "SmartVax Server LOGS", sys.executable, "app.py"], shell=True)
    else:
        process = subprocess.Popen(cmd)

    print("\nWaiting for server to initialize (10 seconds)...")
    for i in range(10, 0, -1):
        print(f"      Starting in {i}...", end='\r')
        time.sleep(1)
    
    print("\n\nChecking if server responded...")
    if check_port(5000):
        print("      SUCCESS: Server is RUNNING at http://127.0.0.1:5000")
        print("      Opening browser now...")
        import webbrowser
        webbrowser.open("http://127.0.0.1:5000")
    else:
        print("      ERROR: Server failed to start on port 5000.")
        print("      Please check the 'SmartVax Server LOGS' window for errors.")
    
    print("\n" + "="*60)
    input("Press ENTER to exit this window...")

if __name__ == "__main__":
    run()
