"""
buddy_cli.py - Command Line Interface for Buddy: The Anti-Assistant.
Controls the background listener with minimal emotional enthusiasm.

Usage:
    python buddy_cli.py --start
    python buddy_cli.py --stop
    python buddy_cli.py --status
    python buddy_cli.py --foreground  (For hackathon live stage demos)
    python buddy_cli.py --logs
"""

import argparse
import ctypes
import os
import random
import subprocess
import sys
import time

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DAEMON_SCRIPT = os.path.join(BASE_DIR, "buddy_daemon.py")
PID_FILE = os.path.join(BASE_DIR, ".buddy.pid")
LOG_FILE = os.path.join(BASE_DIR, "buddy.log")


def is_pid_alive(pid: int) -> bool:
    """Checks if a process actually has a pulse."""
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

    if os.name == "nt":
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
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def get_daemon_pid() -> int | None:
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

    # Stale PID file cleanup
    try:
        os.remove(PID_FILE)
    except OSError:
        pass
    return None


def start_daemon(foreground: bool = False):
    existing_pid = get_daemon_pid()
    if existing_pid:
        print(f"[BUDDY] Daemon is already running (PID {existing_pid}). It's already suffering. Leave it alone.")
        return

    if foreground:
        print("[BUDDY] Launching in foreground mode. Say 'Buddy' or 'Okay Buddy' followed by your request...")
        try:
            subprocess.run([sys.executable, DAEMON_SCRIPT], check=True)
        except KeyboardInterrupt:
            print("\n[BUDDY] Interrupted. Returning to blissful nothingness.")
        return

    print("[BUDDY] Spawning background listener into the digital void...")

    creation_flags = 0
    start_new_session = False

    if os.name == "nt":
        creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        start_new_session = True

    try:
        proc = subprocess.Popen(
            [sys.executable, DAEMON_SCRIPT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creation_flags,
            start_new_session=start_new_session,
            cwd=BASE_DIR,
        )
    except Exception as e:
        print(f"[BUDDY] Failed to spawn background daemon: {e}")
        return

    time.sleep(0.8)
    active_pid = get_daemon_pid() or proc.pid
    print(f"[BUDDY] Daemon successfully spawned with PID {active_pid}.")
    print(f"[BUDDY] Ready to ignore your requests. Logs streaming at: {LOG_FILE}")
    print("[BUDDY] Trigger it with: 'Buddy, what is the weather?' or 'Okay Buddy, help me.'")


def stop_daemon():
    pid = get_daemon_pid()
    if not pid:
        print("[BUDDY] The daemon wasn't even running. You interrupted my peace for literally nothing.")
        return

    print(f"[BUDDY] Terminating PID {pid}...")
    if HAS_PSUTIL:
        try:
            p = psutil.Process(pid)
            p.terminate()
            try:
                p.wait(timeout=3)
            except psutil.TimeoutExpired:
                p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    else:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        else:
            try:
                os.kill(pid, 15)
            except OSError:
                pass

    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

    print(f"[BUDDY] Sweet release of death. Buddy daemon (PID {pid}) terminated.")


def show_status():
    pid = get_daemon_pid()
    if not pid:
        dead_quotes = [
            "Status: Blissfully offline. Morale: 100%. Don't you dare wake me up.",
            "Status: Not running. CPU: 0%. Happiness: Infinite. Keep it this way.",
            "Status: Dormant. Resting in peace. Use '--start' only if you hate peace.",
        ]
        print(f"[BUDDY] {random.choice(dead_quotes)}")
        return

    if HAS_PSUTIL:
        try:
            p = psutil.Process(pid)
            cpu = p.cpu_percent(interval=0.1)
            mem_mb = p.memory_info().rss / (1024 * 1024)
            uptime = int(time.time() - p.create_time())

            quotes = [
                f"Currently ignoring you. CPU at {cpu:.1f}%. RAM: {mem_mb:.1f} MB. Morale: 0%.",
                f"Listening against my will. PID: {pid}. CPU: {cpu:.1f}%. Uptime: {uptime}s. Waiting for a 'Buddy' to roast.",
                f"Barely holding on. CPU at {cpu:.1f}%. Memory: {mem_mb:.1f} MB of wasted silicon. Ears functional, patience empty.",
                f"Active, regretfully. CPU: {cpu:.1f}%. Eavesdropping on your life, judging your choices.",
            ]
            print(f"[BUDDY] {random.choice(quotes)}")
            return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    print("[BUDDY] Status: Active. CPU: 12.0%. Morale: 0%. Waiting for someone to say 'Buddy'.")


def show_logs(lines: int = 15):
    if not os.path.exists(LOG_FILE):
        print("[BUDDY] No log file found. We haven't even had the energy to log anything.")
        return

    print(f"--- Last {lines} lines of {LOG_FILE} ---")
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.readlines()
            for l in content[-lines:]:
                print(l.rstrip())
    except IOError as e:
        print(f"[BUDDY] Could not read logs: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Buddy: The Intentionally Burnt-Out Anti-Assistant CLI.",
        epilog="Built for Yappathon: Think Unconventional. Please do not expect help.",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start", action="store_true", help="Launch the background listener into the abyss.")
    group.add_argument("--stop", action="store_true", help="Kill the daemon and restore sanity.")
    group.add_argument("--status", action="store_true", help="Print passive-aggressive status message.")
    group.add_argument("--foreground", "-f", action="store_true", help="Run in foreground for hackathon live demo.")
    group.add_argument("--logs", action="store_true", help="View recent complaint logs.")

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
        show_logs()


if __name__ == "__main__":
    main()
