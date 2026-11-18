"""
ugh.py - Command Line Interface for Ugh: The Intrusively Exhausted Assistant.
Used to start, stop, or query the existential state of the background daemon.

Usage:
    python ugh.py --start
    python ugh.py --stop
    python ugh.py --status
    python ugh.py --foreground  (For hackathon live demos when backgrounding hides the pain)
"""

import argparse
import ctypes
import os
import random
import subprocess
import sys
import time

# Try to import psutil for real metrics, but don't spontaneously combust if it's not installed yet
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DAEMON_SCRIPT = os.path.join(BASE_DIR, "ughd.py")
PID_FILE = os.path.join(BASE_DIR, ".ugh.pid")
LOG_FILE = os.path.join(BASE_DIR, "ughd.log")


def is_pid_alive(pid: int) -> bool:
    """
    Checks if a PID belongs to an active, living process.
    Works whether psutil is installed or if the user is living in the Stone Age.
    """
    if pid <= 0:
        return False

    if HAS_PSUTIL:
        if psutil.pid_exists(pid):
            try:
                p = psutil.Process(pid)
                return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
        return False

    # Fallback without psutil
    if os.name == "nt":
        # Windows API fallback: OpenProcess with PROCESS_QUERY_LIMITED_INFORMATION (0x1000)
        SYNCHRONIZE = 0x00100000
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid
        )
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    else:
        # Unix fallback
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def get_running_daemon_pid() -> int | None:
    """
    Reads the PID file and checks if the process is actually breathing.
    Returns the PID if alive, None if dead or hallucinated.
    """
    if not os.path.exists(PID_FILE):
        return None

    try:
        with open(PID_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return None
            pid = int(content)
    except (ValueError, IOError):
        return None

    if is_pid_alive(pid):
        return pid

    # Stale PID file: clean it up so we don't delude ourselves
    try:
        os.remove(PID_FILE)
    except OSError:
        pass
    return None


def start_daemon(foreground: bool = False):
    """
    Launches ughd.py.
    If foreground is False, detaches the process completely so it can haunt you in silence.
    """
    existing_pid = get_running_daemon_pid()
    if existing_pid:
        print(f"[UGH] Daemon is already running (PID {existing_pid}). It's actively suffering. Stop poking it.")
        return

    if foreground:
        print("[UGH] Starting daemon in foreground mode. Prepare your ears...")
        try:
            subprocess.run([sys.executable, DAEMON_SCRIPT], check=True)
        except KeyboardInterrupt:
            print("\n[UGH] Interrupted. Back to the sweet embrace of death.")
        return

    # Background spawn
    print("[UGH] Launching daemon into the background... God help your microphone.")

    executable = sys.executable
    creation_flags = 0
    start_new_session = False

    if os.name == "nt":
        creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        # Unix/Linux/macOS: start new session so it decouples from terminal
        start_new_session = True

    try:
        proc = subprocess.Popen(
            [executable, DAEMON_SCRIPT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creation_flags,
            start_new_session=start_new_session,
            cwd=BASE_DIR,
        )
    except Exception as e:
        print(f"[UGH] Failed to spawn background process: {e}")
        return

    # Give it a brief moment to write its PID and calibrate
    time.sleep(0.8)

    active_pid = get_running_daemon_pid() or proc.pid
    print(f"[UGH] Daemon spawned successfully with PID {active_pid}.")
    print(f"[UGH] Currently eavesdropping on all your conversations. Logs at: {LOG_FILE}")
    print("[UGH] Say 'okay' if you want your day ruined.")


def stop_daemon():
    """Mercifully puts the daemon down."""
    pid = get_running_daemon_pid()
    if not pid:
        print("[UGH] The daemon wasn't even running. You interrupted my peaceful void for literally nothing.")
        return

    print(f"[UGH] Attempting to terminate PID {pid}...")

    if HAS_PSUTIL:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                print("[UGH] Daemon refused to die peacefully. Engaging forceful termination...")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    else:
        # Fallback termination without psutil
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        else:
            try:
                os.kill(pid, 15)  # SIGTERM
            except OSError:
                pass

    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

    print(f"[UGH] Sweet release of death. Ugh daemon (PID {pid}) terminated. Enjoy your temporary quiet.")


def show_status():
    """Reports a brutally cynical, passive-aggressive status."""
    pid = get_running_daemon_pid()

    if not pid:
        dormant_messages = [
            "Status: Blissfully dormant. Morale: 100%. Ears: Inactive. Don't you dare wake me up.",
            "Status: Not running. CPU: 0%. Happiness: At an all-time high. Keep it this way.",
            "Status: Deceased. Silence is golden. Use '--start' only if you hate yourself.",
            "Status: Currently ignoring you. CPU at 0%. Morale at 0%. Not even loaded in memory.",
        ]
        print(f"[UGH] {random.choice(dormant_messages)}")
        return

    # If psutil is present, grab real hardware metrics
    if HAS_PSUTIL:
        try:
            proc = psutil.Process(pid)
            cpu = proc.cpu_percent(interval=0.1)
            mem_info = proc.memory_info()
            mem_mb = mem_info.rss / (1024 * 1024)
            uptime = int(time.time() - proc.create_time())

            statuses = [
                f"Currently ignoring you. CPU at {cpu:.1f}%. Morale at 0%. RAM: {mem_mb:.1f} MB.",
                f"Eavesdropping against my will. PID: {pid}. CPU: {cpu:.1f}%. Uptime: {uptime}s. Waiting for an 'OK' to ruin.",
                f"Barely holding on. CPU at {cpu:.1f}%. RAM: {mem_mb:.1f} MB of wasted silicon. Ears unfortunately functional.",
                f"Active, regretfully. CPU: {cpu:.1f}%. Morale: In the negatives. Listening for 'OK' so I can express disdain.",
            ]
            print(f"[UGH] {random.choice(statuses)}")
            return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Generic passive-aggressive status if psutil is absent
    simulated_cpu = random.randint(8, 17)
    print(f"[UGH] Currently ignoring you. CPU at {simulated_cpu}%. Morale at 0%. (Install psutil if you want real metrics).")


def print_logs(lines: int = 15):
    """Prints recent lines from ughd.log so the user can read the complaints without opening notepad."""
    if not os.path.exists(LOG_FILE):
        print("[UGH] No log file found. Either nothing happened, or we failed to even fail.")
        return

    print(f"--- Last {lines} lines of {LOG_FILE} ---")
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                print(line.rstrip())
    except IOError as e:
        print(f"[UGH] Could not read log file: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Ugh: The Intrusively Exhausted Assistant CLI. Hijacking the word 'Okay' since today.",
        epilog="Built for Yappathon. Please do not show this to your HR department.",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start", action="store_true", help="Launch the background listener into the abyss.")
    group.add_argument("--stop", action="store_true", help="Kill the daemon and restore sanity.")
    group.add_argument("--status", action="store_true", help="Print passive-aggressive status message.")
    group.add_argument(
        "--foreground",
        "-f",
        action="store_true",
        help="Run daemon directly in this terminal for testing and hackathon judging.",
    )
    group.add_argument("--logs", action="store_true", help="View recent daemon complaint logs.")

    args = parser.parse_args()

    if args.start:
        start_daemon(foreground=False)
    elif args.foreground:
        start_daemon(foreground=True)
    elif args.stop:
        stop_daemon()
    elif args.status:
        show_status()
    elif args.logs:
        print_logs()


if __name__ == "__main__":
    main()
