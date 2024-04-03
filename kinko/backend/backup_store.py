import json 
from enum import Enum

class BackupStatusCodes(Enum):
    Idle = 0
    Running = 1

class BackupStatus():
    def __init__(self):
        self.last_backup = None
        self.last_refreshed = None
        self.status_code = BackupStatusCodes.Idle
        self.progress = 0
        self.message = ""
        self.backups = []

class BackupSettings():
    def __init__(self, id, name,  repository_password, remote):
        self.id = id
        self.name = name
        self.repository_password = repository_password
        self.remote = remote

class BackupConfig():
    def __init__(self, settings, status):
        self.settings = settings
        self.status = status 
    
class BackupStore():
    backup_configs = []

    def upsert_backup_config(self, backup_config):
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