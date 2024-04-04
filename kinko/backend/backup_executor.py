import threading
import time
import backend.restic as restic
from datetime import datetime, timezone, timedelta
import os
import timeago
from enum import Enum
from backend.backup_store import BackupStatusCodes, BackupStatus, BackupSettings, BackupConfig
from event_monitors.system_status import PowerSaverStatus, NetworkStatus
import flatpak.api

REFRESH_INTERVAL = 600

class BackupExecutor():
    def __init__(self, backup_store, system_status):
        self.backup_store = backup_store
        self.system_status = system_status
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()

    def get_next_backup_time(self, id):
        backup_config = self.backup_store.get_backup_config(id)
        if backup_config is None:
            return None

        time = None
        if backup_config.status.last_backup != None:
            time = backup_config.status.last_backup + timedelta(hours=1)
        else:
            time = datetime.now(timezone.utc)

        # if in past, check battery and network
        if time <= datetime.now(timezone.utc):
            if self.system_status.network_status == NetworkStatus.METERED:
                return "metered"
            if self.system_status.power_saver_status == PowerSaverStatus.Enabled:
                return "powersaver"
            return "now"

        return timeago.format(time, datetime.now(timezone.utc))

    def run(self):
        time.sleep(10)
        last_refreshed = datetime.fromtimestamp(0)
        while True:
            is_running = False
            for backup_config in self.backup_store.get_backup_configs():
                if backup_config.status.status_code == BackupStatusCodes.Running:
                    is_running = True
                    break
            if is_running:
                flatpak.api.set_status("Running Backup...")
            else:
                flatpak.api.set_status("Idle")

            for backup_config in self.backup_store.get_backup_configs():
                if backup_config.status.last_refreshed == None or (datetime.now() - backup_config.status.last_refreshed).total_seconds() > REFRESH_INTERVAL:
                    print("refreshing backups")
                    self.refresh_backups()
                    print("refreshed backups")
                    break

            for backup_config in self.backup_store.get_backup_configs():
                if backup_config.status.status_code != BackupStatusCodes.Idle:
                    continue

                next_backup = self.get_next_backup_time(backup_config.settings.id)
                if next_backup == "now":
                    print("now with status", backup_config.status.status_code)
                    backup_config.status.status_code = BackupStatusCodes.Running
                    self.backup_now(backup_config.settings.id)
            time.sleep(5)

    def refresh_backups(self):
        for backup_config in self.backup_store.get_backup_configs():
            try:
                snapshots = restic.snapshots(backup_config.settings.remote, backup_config.settings.repository_password)
                if len(snapshots) > 0:
                    backup_config.status.last_backup = datetime.fromisoformat(snapshots[-1].get("time"))
                else:
                    backup_config.status.last_backup = None

                for snapshot in snapshots:
                    snapshot["time"] = datetime.fromisoformat(snapshot.get("time"))

                backup_config.status.backups = snapshots
                backup_config.status.last_refreshed = datetime.now()
            except Exception as e:
                print("Error getting snapshots", e)

    def backup_now(self, id):
        thread = threading.Thread(target=self.run_backup, args=(id,))
        thread.start()

    def get_backups(self, id):
        backup_config = self.backup_store.get_backup_config(id)
        if backup_config is None:
            return []
        snapshots = restic.snapshots(backup_config.settings.get_restic_repo(), backup_config.settings.s3_access_key, backup_config.settings.s3_secret_key, backup_config.settings.repository_password)
        return snapshots

    def run_backup(self, id):
        backup_config = self.backup_store.get_backup_config(id)

        if backup_config is None:
            return False

        backup_config.status.progress = 0
        backup_config.status.message = "Starting backup"
        print("Starting backup")

        def on_progress(status):
            if status.get("message_type") == "status":
                backup_config.status.message = "Backing up..."
                backup_config.status.progress = status.get("percent_done")
                print("progress", status.get("percent_done"))
                   
            if status.get("message_type") == "summary":
                print("backup complete progress")
                backup_config.status.last_backup = datetime.now(timezone.utc)
                backup_config.status.status = BackupStatusCodes.Idle
                backup_config.status.message = "Idle"

        ignores = []
        ignores.append(".cache/")
        ignores.append("Code/Cache*")
        ignores.append("Cache")
        ignores.append("cache")
        ignores.append(".thumbnails/")
        ignores.append("node_modules/")
        ignores.append("__pycache__/")
        ignores.append("site-packages/")
        ignores.append(".npm/")
        ignores.append(".mozilla/firefox/")
        ignores.append(".vscode/extensions/")
        ignores.append(".wine")
        ignores.append("go/pkg/mod/")
        ignores.append(".git/objects/pack/")
        ignores.append(".rustup/")
        ignores.append(".local/share/Trash/")
        ignores.append("Downloads")
        ignores.append("Videos")
        ignores.append("*.mp4")
        ignores.append("*.mov")
        ignores.append("*.avi")
        ignores.append("*.wmv")
        ignores.append("*.mkv")
        ignores.append("*.flv")
        ignores.append("*.webm")
        ignores.append("*.vmx")
        ignores.append("*.vmxf")
        ignores.append("*.vmdk")
        ignores.append("*.nvram")
        ignores.append("*.vmem")
        ignores.append("*.vmsd")
        ignores.append("*.vmsn")
        ignores.append("*.vmswp")
        ignores.append("*.vmss")
        ignores.append("*.qcow2")
        ignores.append(".local/share/containers/")

        try:
            homedir = os.path.expanduser('~')
            restic.backup(backup_config.settings.remote, backup_config.settings.repository_password, homedir, ignores, on_progress=on_progress)
            backup_config.status.status_code = BackupStatusCodes.Idle
            backup_config.status.message = "Idle"
        except Exception as e:
            print("error running backup", e)
            return False

        print("Backup complete")
        self.refresh_backups()
        return True