import json 

class BackupStatus():
    def __init__(self):
        self.last_backup = None
        self.last_refreshed = None
        self.status = "Idle"
        self.status_message = "Idle"
        self.progress = 0
        self.files = 0
        self.max_files = 0
        self.bytes_processed = 0
        self.bytes_total = 0
        self.seconds_elapsed = 0
        self.seconds_remaining = 0
        self.message = ""
        self.backups = []

class BackupSchedule():
    def __init__(self):
        self.allow_on_metered = True
        self.on_network = False
        self.on_ac = True
        self.backup_schedule_enabled = True
        self.backup_frequency = "hourly"
        self.cleanup_schedule_enabled = True
        self.cleanup_frequency = "daily"
        self.cleanup_keep_hourly = 2
        self.cleanup_keep_daily = 1
        self.cleanup_keep_weekly = 0
        self.cleanup_keep_monthly = 0
        self.cleanup_keep_yearly = 0

class BackupSettings():
    def __init__(self, id, name, s3_secret_key, s3_access_key, s3_repository, repository_password, sources):
        self.id = id
        self.name = name
        self.s3_secret_key = s3_secret_key
        self.s3_access_key = s3_access_key
        self.s3_repository = s3_repository
        self.repository_password = repository_password
        self.sources = sources
        self.ignores_cache = True
        self.ignore_trash = True
        self.ignore_downloads = True
        self.ignore_videos = True
        self.ignore_vms = True
    
    def get_restic_repo(self):
        return "s3:" + self.s3_repository

class BackupConfig():
    def __init__(self, settings, status, schedule):
        self.settings = settings
        self.status = status 
        self.schedule = schedule
    
class BackupStore():
    backup_configs = []
    update_listeners = []

    def add_backup_config(self, backup_config):
        # replace if same id
        for i, b in enumerate(self.backup_configs):
            if b.settings.id == backup_config.settings.id:
                status = self.backup_configs[i].status
                backup_config.status = status
                self.backup_configs[i] = backup_config
                return
        self.backup_configs.append(backup_config)
    
    def get_backup_configs(self):
        return self.backup_configs
    
    def get_backup_config(self, id):
        for backup_config in self.backup_configs:
            if backup_config.settings.id == id:
                return backup_config
        return None
    
    def remove_backup_config(self, id):
        for backup_config in self.backup_configs:
            if backup_config.settings.id == id:
                self.backup_configs.remove(backup_config)
                return True
        return False
    
    def on_update(self, callback):
        self.update_listeners.append(callback)

    def notify_update(self):
        for callback in self.update_listeners:
            callback()