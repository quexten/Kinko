#!/usr/bin/python
import backend.backup_store as backup_store
import backend.backup_executor as backup_executor
from event_monitors.system_status import SystemStatus
import backend.config as config
import sys
import ipc
import os
import subprocess
import time
import threading
import socket
import flatpak.api

def glib_main():
    print("GLib main loop started")
    from gi.repository import GLib, Gio
    m = GLib.MainLoop()
    m.run()

def daemonize():
    system_status = SystemStatus()
    system_status.start_monitors()

    # load config
    b = backup_store.BackupStore()
    configs = config.read_all_configs()

    for cfg in configs:
        b.upsert_backup_config(cfg)

    # start event monitors & backup executor
    be = backup_executor.BackupExecutor(b, system_status)
    thread = threading.Thread(target=glib_main)
    thread.start()
    print("waiting for ipc...")
    ipc.daemonize(b, be)

flatpak.api.register_autostart(True)

is_thread = True
try:
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    conn.connect(os.path.expanduser("~") + "/.kinko.sock")
    is_thread = False
    print("Daemon already running, exiting...")
except:
    print("Daemon not running, starting...")
    if os.path.exists(os.path.expanduser("~") + "/.kinko.sock"):
        os.remove(os.path.expanduser("~") + "/.kinko.sock")
    print("Starting daemon thread...")
    thread = threading.Thread(target=daemonize)
    thread.start()

time.sleep(1)

if not "--hidden" in sys.argv:
    print("Starting UI...")
    subprocess.Popen(["python3", "/app/bin/kinko_ui.py"])

if is_thread:
    print("Waiting for daemon thread...")
    while True: 
        time.sleep(1)