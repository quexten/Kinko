#!/usr/bin/python
import backend.backup_store as backup_store
import backend.backup_executor as backup_executor
import event_monitors.power_monitor as power_monitor
import event_monitors.network_monitor as network_monitor
import backend.config as config
import sys
import ipc
import os
import subprocess
import time
import threading
import socket

def glib_main():
    print("GLib main loop started")
    from gi.repository import GLib, Gio
    m = GLib.MainLoop()
    m.run()

def daemonize():
    # load config
    b = backup_store.BackupStore()
    configs = config.read_all_configs()

    for cfg in configs:
        b.add_backup_config(cfg)

    # start event monitors & backup executor
    be = backup_executor.BackupExecutor(b)
    power_monitor.start_monitor(be)
    network_monitor.start_monitor(be)
    thread = threading.Thread(target=glib_main)
    thread.start()
    print("waiting for ipc...")
    ipc.daemonize(b, be)


if "daemonize" in sys.argv:
    daemonize()
    os._exit(0)

is_flatpak = os.path.exists("/.flatpak-info")
if is_flatpak:
    print("Running in flatpak, registering with background portal for autostart.")
    try:
        subprocess.Popen(["python3", "/app/bin/autostart.py"], start_new_session=True)
    except:
        pass

is_thread = True
try:
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    conn.connect(os.path.expanduser("~") + "/.kinko.sock")
except:
    if os.path.exists(os.path.expanduser("~") + "/.kinko.sock"):
        os.remove(os.path.expanduser("~") + "/.kinko.sock")
    print("Starting daemon thread...")
    thread = threading.Thread(target=daemonize)
    thread.start()

time.sleep(1)

is_silent = "--silent" in sys.argv
if not is_silent:
    if os.path.exists("/app/bin/kinko_ui.py"):
        subprocess.Popen(["python3", "/app/bin/kinko_ui.py"])

if is_thread:
    print("Waiting for daemon thread...")
    while True:
        time.sleep(1)