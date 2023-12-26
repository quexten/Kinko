#!/usr/bin/python
import backend.backup_store as backup_store
import backend.backup_executor as backup_executor
import event_monitors.power_monitor as power_monitor
import event_monitors.network_monitor as network_monitor
import event_monitors.memory_monitor
import backend.config as config
import app
import subprocess
import sys
import time

# load config
b = backup_store.BackupStore()
configs = config.read_all_configs()

for cfg in configs:
    b.add_backup_config(cfg)

# start event monitors & backup executor
be = backup_executor.BackupExecutor(b)
power_monitor.start_monitor(be)
network_monitor.start_monitor(be)

try:
    subprocess.Popen(["python3", "/app/bin/autostart.py"], start_new_session=True)
except:
    pass

is_silent = "--silent" in sys.argv
app.run(b, be, is_silent)
