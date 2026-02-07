import os
import time
import subprocess
import threading
import re
import psutil
import json
import signal
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from pathlib import Path
import socket
import webbrowser

# --- CONFIGURATION ---
# Force current directory to be where the script is
CURRENT_DIR = Path(__file__).resolve().parent
os.chdir(CURRENT_DIR)

# Use 'config.json' as the standard file name
CONFIG_FILE = CURRENT_DIR / "config.json"

app = Flask(__name__, template_folder=str(CURRENT_DIR / "templates"))
CORS(app)

# Global variables
server_process = None
java_proc_obj = None  # Persist the Java process object to fix CPU reading
player_list = set()
console_buffer = []

# --- CONFIG MANAGEMENT (IMPROVED) ---

def load_config():
    """
    Load configuration from disk. 
    Always re-reads the file to ensure the API uses updated paths from the Bash sync.
    """
    defaults = {
        "start_script": str(CURRENT_DIR / "start.sh"), 
        "server_dir": str(CURRENT_DIR / "Server"),
        "max_ram": 12
    }

    if not CONFIG_FILE.exists():
        # If config doesn't exist, we use defaults but don't save yet 
        # to let the bash script handle the first sync
        return defaults
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            # Merge with defaults to ensure all keys exist
            return {**defaults, **data}
    except Exception as e:
        print(f"⚠️ Error loading config: {e}")
        return defaults

def save_config(data):
    """Save configuration to disk"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"❌ Error saving config: {e}")

# Initial load
GLOBAL_CONFIG = load_config()

print(f"--- SYSTEM STARTED ---")
print(f"📂 Config loaded. Target: {GLOBAL_CONFIG['start_script']}")
print(f"------------------------")

# --- SERVER FUNCTIONS ---

def get_server_ip():
    """Get the server's public IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def find_ghost_process():
    """Find any lingering Hytale Java processes"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'java' in proc.info['name'].lower():
                cmd = ' '.join(proc.info['cmdline'] or [])
                if 'HytaleServer.jar' in cmd:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

def start_server_internal():
    global server_process, player_list, console_buffer, java_proc_obj
    
    # Reload config immediately before starting to get the latest synced paths
    current_conf = load_config()
    start_script_path = Path(current_conf['start_script'])
    working_dir = start_script_path.parent

    if server_process and server_process.poll() is None:
        return {"success": False, "error": "Server already running"}

    ghost = find_ghost_process()
    if ghost:
        return {
            "success": False, 
            "error": f"Server already running (PID {ghost.pid}). Stop first."
        }

    if not start_script_path.exists():
        return {"success": False, "error": f"File not found: {start_script_path}"}

    try:
        # Reset tracker variables
        java_proc_obj = None
        player_list = set()
        console_buffer = []

        # Start the process
        server_process = subprocess.Popen(
            ["bash", str(start_script_path)], 
            cwd=str(working_dir),                 
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=os.setsid
        )
        
        threading.Thread(target=monitor_output, args=(server_process,), daemon=True).start()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def stop_server_force():
    global server_process, java_proc_obj
    killed_something = False

    if server_process and server_process.poll() is None:
        try:
            server_process.stdin.write("stop\n")
            server_process.stdin.flush()
            time.sleep(3)
        except: pass

        if server_process.poll() is None:
            try:
                os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
                killed_something = True
            except: pass
    
    ghost = find_ghost_process()
    if ghost:
        try:
            ghost.terminate()
            time.sleep(1)
            if ghost.is_running():
                ghost.kill()
            killed_something = True
        except: pass

    server_process = None
    java_proc_obj = None 
    return killed_something

def monitor_output(proc):
    global player_list
    while True:
        line = proc.stdout.readline()
        if not line: break
        clean_line = line.strip()
        if clean_line:
            console_buffer.append(clean_line)
            if len(console_buffer) > 200: console_buffer.pop(0)
            
            if "Adding player" in clean_line:
                match = re.search(r"player '([^'\s]+)", clean_line)
                if match: player_list.add(match.group(1))

            if "Removing player" in clean_line or "left world" in clean_line:
                match = re.search(r"player '([^'\s]+)", clean_line)
                if match and match.group(1) in player_list:
                    player_list.remove(match.group(1))

def send_command_internal(cmd):
    global server_process
    if server_process and server_process.poll() is None:
        try:
            server_process.stdin.write(cmd + "\n")
            server_process.stdin.flush()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return {"success": False, "error": "Server offline."}

# --- API ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    global java_proc_obj, server_process
    
    # Reload config for RAM max value display
    current_conf = load_config()

    status_str = "stopped"
    cpu = 0.0
    mem_gb = 0.0
    uptime = 0
    server_ip = get_server_ip()
    
    if server_process and server_process.poll() is None:
        status_str = "running"
        try:
            if java_proc_obj is None or not java_proc_obj.is_running():
                parent = psutil.Process(server_process.pid)
                children = parent.children(recursive=True)
                for child in children:
                    if "java" in child.name().lower():
                        java_proc_obj = child 
                        java_proc_obj.cpu_percent(interval=None) 
                        break
            
            if java_proc_obj and java_proc_obj.is_running():
                with java_proc_obj.oneshot():
                    raw_cpu = java_proc_obj.cpu_percent(interval=None)
                    if raw_cpu == 0.0:
                         raw_cpu = java_proc_obj.cpu_percent(interval=0.1)
                    
                    # FIX: Normalize CPU by core count
                    cpu_count = psutil.cpu_count() or 1
                    cpu = raw_cpu / cpu_count
                         
                    mem_gb = java_proc_obj.memory_info().rss / (1024**3)
                    uptime = int(time.time() - java_proc_obj.create_time())
            else:
                java_proc_obj = None

        except Exception:
            java_proc_obj = None

    else:
        ghost = find_ghost_process()
        if ghost:
            status_str = "ghost"

    return jsonify({
        "server": {"status": status_str, "uptime_s": uptime, "ip": server_ip},
        "stats": {
            "cpu": round(cpu, 1),
            "ram_usage_gb": round(mem_gb, 2),
            "ram_max_gb": current_conf['max_ram'],
            "ram_percent": round((mem_gb / float(current_conf['max_ram'])) * 100, 1) if current_conf['max_ram'] > 0 else 0
        },
        "players": {"count": len(player_list), "list": list(player_list)}
    })

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return jsonify(load_config())
    
    new_data = request.json
    # Validation
    path_chk = Path(new_data.get('start_script', ''))
    if not path_chk.is_absolute():
        path_chk = CURRENT_DIR / path_chk

    if not path_chk.exists():
        return jsonify({"success": False, "error": "Invalid start.sh path"})
        
    save_config(new_data)
    return jsonify({"success": True})

@app.route('/api/control/<action>', methods=['POST'])
def control(action):
    if action == "start": 
        return jsonify(start_server_internal())
    elif action == "stop": 
        stop_server_force()
        return jsonify({"success": True})
    return jsonify({"error": "Invalid action"})

@app.route('/api/command', methods=['POST'])
def command():
    return jsonify(send_command_internal(request.json.get('command')))

@app.route('/api/logs')
def logs():
    return jsonify({"lines": console_buffer[-100:]})

def cleanup_handler(signum, frame):
    print("\nShutting down Dashboard...")
    stop_server_force()
    exit(0)

signal.signal(signal.SIGINT, cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)

def open_browser_once():
    time.sleep(1.5)
    print("🌐 Opening Dashboard: http://localhost:5000")
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    threading.Thread(target=open_browser_once, daemon=True).start()
    # Host 0.0.0.0 allows LAN access
    app.run(host='0.0.0.0', port=5000, debug=False)