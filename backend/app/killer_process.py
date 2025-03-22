import subprocess
import time
import sys
import os


def kill_processes_on_port(port=8000):
    """Kill all processes listening on the specified port."""
    print(f"Checking for processes using port {port}...")

    try:
        # uniquement pour windows
        if os.name == 'nt':
            # Find PIDs using the port
            netstat = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            if not netstat:
                print(f"No processes found using port {port}")
                return True

            # Extract PIDs
            pids = set()
            for line in netstat.split('\n'):
                if line.strip():
                    parts = [p for p in line.strip().split(' ') if p]
                    if len(parts) >= 5:
                        pids.add(parts[4])

            # Kill each process
            for pid in pids:
                try:
                    subprocess.check_output(f'taskkill /F /PID {pid}', shell=True)
                    print(f"Killed process {pid} using port {port}")
                except subprocess.CalledProcessError:
                    print(f"Failed to kill process {pid}")

        # pour Linux/Mac
        else:
            cmd = f"lsof -i :{port} | grep LISTEN | awk '{{print $2}}'"
            pids = subprocess.check_output(cmd, shell=True).decode().strip().split('\n')

            if not pids or pids[0] == '':
                print(f"No processes found using port {port}")
                return True

            for pid in pids:
                if pid:
                    subprocess.check_output(f'kill -9 {pid}', shell=True)
                    print(f"Killed process {pid} using port {port}")

        # Verify the port is now free
        time.sleep(1)
        return check_port_available(port)

    except subprocess.CalledProcessError as e:
        print(f"No processes found using port {port}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def check_port_available(port):
    """Check if the port is available."""
    try:
        if os.name == 'nt':
            netstat = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            return netstat.strip() == ""
        else:
            cmd = f"lsof -i :{port} | grep LISTEN"
            output = subprocess.check_output(cmd, shell=True).decode()
            return output.strip() == ""
    except subprocess.CalledProcessError:
        # If the command fails, it likely means no process is using the port
        return True
    except Exception as e:
        print(f"Error checking port availability: {str(e)}")
        return False


