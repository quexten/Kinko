import threading
import time
import backend.restic as restic
from datetime import datetime, timezone
import os

class BackupExecutor():
    def __init__(self, backup_store):
        self.backup_store = backup_store
        self.network_status = "unmetered"
        self.network_status_last_changed = None
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()

    def notify(self, event):
        if event == "power_on":
            print("plugged in, running backups...")
            for backup_config in self.backup_store.get_backup_configs():
                if backup_config.status.status == "Running":
                    continue
                if backup_config.schedule.on_ac:
                    self.backup_now(backup_config.settings.id)
        if event == "network_connected_metered":
            if self.network_status == "metered":
                return
            self.network_status = "metered"
            self.network_status_last_changed = datetime.now()
            print("connected to metered network, running backups...")
        if event == "network_connected_unmetered":
            if self.network_status == "unmetered":
                return
            self.network_status = "unmetered"
            self.network_status_last_changed = datetime.now()
            print("connected to unmetered network, running backups...")
        if event == "network_disconnected":
            if self.network_status == "disconnected":
                return
            self.network_status = "disconnected"
            self.network_status_last_changed = datetime.now()

    def run(self):
        time.sleep(5)
        last_refreshed = datetime.fromtimestamp(0)
        while True:
            for backup_config in self.backup_store.get_backup_configs():
                if backup_config.status.last_refreshed == None or (datetime.now() - backup_config.status.last_refreshed).total_seconds() > 60:
                    self.refresh_backups()
                    break
            
            # check network changed time
            if self.network_status_last_changed != None and (datetime.now() - self.network_status_last_changed).total_seconds() > 5:
                self.network_status_last_changed = None
                for backup_config in self.backup_store.get_backup_configs():
                    if backup_config.status.status == "Running":
                        continue
                    if backup_config.schedule.backup_schedule_enabled and backup_config.schedule.on_network:
                        if backup_config.schedule.allow_on_metered or self.network_status == "unmetered":
                            self.backup_now(backup_config.settings.id)

            # check schedules
            for backup_config in self.backup_store.get_backup_configs():
                if backup_config.status.status != "Idle":
                    continue
                if backup_config.schedule.backup_schedule_enabled and backup_config.status.last_backup != None:
                    if backup_config.schedule.backup_frequency == "hourly":
                        if (datetime.now(timezone.utc) - backup_config.status.last_backup).total_seconds() > 60 * 60:
                            self.backup_now(backup_config.settings.id)
                    if backup_config.schedule.backup_frequency == "daily":
                        if (datetime.now(timezone.utc) - backup_config.status.last_backup).total_seconds() > 60 * 60 * 24:
                            self.backup_now(backup_config.settings.id)
                    if backup_config.schedule.backup_frequency == "weekly":
                        if (datetime.now(timezone.utc) - backup_config.status.last_backup).total_seconds() > 60 * 60 * 24 * 7:
                            self.backup_now(backup_config.settings.id)
                if backup_config.schedule.cleanup_schedule_enabled and backup_config.status.last_backup == None:
                    self.backup_now(backup_config.settings.id)
            time.sleep(5)

    def refresh_backups(self):
        for backup_config in self.backup_store.get_backup_configs():
            try:
                snapshots = restic.snapshots(backup_config.settings.get_restic_repo(), backup_config.settings.s3_access_key, backup_config.settings.s3_secret_key, backup_config.settings.repository_password)
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
        self.backup_store.notify_update()

    def restore_now(self, id, snapshot_id, mountpoint, include, exclude, destination):
        thread = threading.Thread(target=self.run_restore, args=(id, snapshot_id, mountpoint, include, exclude, destination))
        thread.start()

    def run_restore(self, id, snapshot_id, mountpoint, include, exclude, destination):
        backup_config = self.backup_store.get_backup_config(id)
        if backup_config is None:
            return False
        backup_config.status.status = "Running"
        backup_config.status.progress = 0
        backup_config.status.message = "Starting restore"
        backup_config.status.status_message = "Starting restore"
        backup_config.status.files = 0
        backup_config.status.max_files = 0
        backup_config.status.bytes_processed = 0
        backup_config.status.bytes_total = 0
        backup_config.status.seconds_elapsed = 0
        backup_config.status.seconds_remaining = None
        print("Starting restore")

        def on_progress(status):
            if status.get("message_type") == "status":
                backup_config.status.progress = status.get("percent_done")
                backup_config.status.message = "Restoring..."
                backup_config.status.status_message = "Restoring..."
                backup_config.status.files = status.get("files_done")
                if "files_restored" in status:
                    backup_config.status.files = status.get("files_restored")
                backup_config.status.max_files = status.get("total_files")
                backup_config.status.bytes_processed = status.get("bytes_done")
                if "bytes_restored" in status:
                    backup_config.status.bytes_processed = status.get("bytes_restored")
                backup_config.status.bytes_total = status.get("total_bytes")
                backup_config.status.seconds_elapsed = status.get("seconds_elapsed")
                backup_config.status.seconds_remaining = status.get("seconds_remaining")
                if status.get("percent_done") == 1:
                    backup_config.status.message = "Restore complete"
                    backup_config.status.status = "Idle"
                   
            if status.get("message_type") == "summary":
                backup_config.status.status = "Idle"
                backup_config.status.message = "Restore complete"
                backup_config.status.status_message = "Idle"
                self.backup_store.notify_update()

        try:
            restic.restore(backup_config.settings.get_restic_repo(), backup_config.settings.s3_access_key, backup_config.settings.s3_secret_key, backup_config.settings.repository_password, snapshot_id, mountpoint, include, exclude, destination, on_progress=on_progress)
        except Exception as e:
            backup_config.status.status = "Error"
            backup_config.status.message = "Restore failed"
            backup_config.status.status_message = e
            print("error running restore", e)
            return False

        backup_config.status.status = "Idle"
        backup_config.status.message = "Restore complete"
        backup_config.status.status_message = "Idle"

        print("Restore complete")
        return True

    def backup_now(self, id):
        thread = threading.Thread(target=self.run_backup, args=(id,))
        thread.start()

    def get_backups(self, id):
        backup_config = self.backup_store.get_backup_config(id)
        if backup_config is None:
            return []
        snapshots = restic.snapshots(backup_config.settings.get_restic_repo(), backup_config.settings.s3_access_key, backup_config.settings.s3_secret_key, backup_config.settings.repository_password)
        return snapshots
    
    def run_clean(self, id):
        for backup_config in self.backup_store.get_backup_configs():
            if backup_config.settings.id == id:
                backup_config.status.status = "Running-Cleanup"
                backup_config.status.message = "Cleaning up"
                backup_config.status.status_message = "Cleaning up"
                try:
                    backup_config.status.message = "Unlocking repository"
                    backup_config.status.status_message = "Unlocking repository"
                    restic.unlock(backup_config.settings.get_restic_repo(), backup_config.settings.s3_access_key, backup_config.settings.s3_secret_key, backup_config.settings.repository_password)
                    backup_config.status.message = "Doing cleanup"
                    backup_config.status.status_message = "Doing cleanup"
                    res = restic.forget(backup_config.settings.get_restic_repo(), backup_config.settings.s3_access_key, backup_config.settings.s3_secret_key, backup_config.settings.repository_password, int(backup_config.schedule.cleanup_keep_hourly), int(backup_config.schedule.cleanup_keep_daily), int(backup_config.schedule.cleanup_keep_weekly), int(backup_config.schedule.cleanup_keep_monthly), int(backup_config.schedule.cleanup_keep_yearly))
                    backup_config.status.message = "Refreshing backups"
                    backup_config.status.status_message = "Refreshing backups"
                    self.refresh_backups()
                except Exception as e:
                    print("error cleaning up", e)
                    backup_config.status.status = "Error"
                backup_config.status.status = "Idle"
                return True

    def clean_now(self, id):
        thread = threading.Thread(target=self.run_clean, args=(id,))
        thread.start()

    def run_backup(self, id):
        backup_config = self.backup_store.get_backup_config(id)
        if backup_config is None:
            return False

        if backup_config.status.status != "Idle":
            return False

        backup_config.status.status = "Running"
        backup_config.status.progress = 0
        backup_config.status.message = "Starting backup"
        backup_config.status.status_message = "Starting Backup..."
        backup_config.status.files = 0
        backup_config.status.max_files = 0
        backup_config.status.bytes_processed = 0
        backup_config.status.bytes_total = 0
        backup_config.status.seconds_elapsed = 0
        backup_config.status.seconds_remaining = None
        print("Starting backup")

        def on_progress(status):
            if status.get("message_type") == "status":
                backup_config.status.message = "Backing up..."
                backup_config.status.progress = status.get("percent_done")
                if status.get("current_files") is not None and len(status.get("current_files")) > 0:
                    backup_config.status.status_message = "" + status.get("current_files")[0]
                else:
                    backup_config.status.status_message = "Backing up..."
                backup_config.status.files = status.get("files_done")
                backup_config.status.max_files = status.get("total_files")
                backup_config.status.bytes_processed = status.get("bytes_done")
                backup_config.status.bytes_total = status.get("total_bytes")
                backup_config.status.seconds_remaining = status.get("seconds_remaining")
                if status.get("percent_done") == 1:
                    backup_config.status.last_backup = datetime.now(timezone.utc)
                    backup_config.status.message = "Backup complete"
                    backup_config.status.status_message = "Idle"
                    backup_config.status.status = "Idle"
                   
            if status.get("message_type") == "summary":
                backup_config.status.last_backup = datetime.now(timezone.utc)
                backup_config.status.status = "Idle"
                backup_config.status.message = "Backup complete"
                backup_config.status.status_message = "Idle"
                self.backup_store.notify_update()

        ignores = []
        if backup_config.settings.ignores_cache:
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
        if backup_config.settings.ignore_trash:
            ignores.append(".local/share/Trash/")
        if backup_config.settings.ignore_downloads:
            ignores.append("Downloads")
        if backup_config.settings.ignore_videos:
            ignores.append("Videos")
            ignores.append("*.mp4")
            ignores.append("*.mov")
            ignores.append("*.avi")
            ignores.append("*.wmv")
            ignores.append("*.mkv")
            ignores.append("*.flv")
            ignores.append("*.webm")
        if backup_config.settings.ignore_vms:
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
            restic.backup(backup_config.settings.get_restic_repo(), backup_config.settings.s3_access_key, backup_config.settings.s3_secret_key, backup_config.settings.repository_password, backup_config.settings.sources[0].replace("~", os.path.expanduser('~')) , ignores, on_progress=on_progress)
            backup_config.status.status = "Idle"
            backup_config.status.message = "Backup complete"
            backup_config.status.status_message = "Idle"
        except Exception as e:
            backup_config.status.status = "Error"
            backup_config.status.message = "Backup failed"
            print("error running backup", e)
            return False

        print("Backup complete")
        self.refresh_backups()
        return True