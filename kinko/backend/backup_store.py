import json 
from enum import Enum
from backend.remotes import ResticRemote
from typing import List

class BackupStatusCodes(Enum):
    Idle = 0
    Running = 1

class BackupStatus():
    def __init__(self):
        self.last_backup = None
        self.last_refreshed = None
        self.status_code = BackupStatusCodes.Idle
        self.progress = 0
        self.seconds_elapsed = 0
        self.seconds_remaining = 0
        self.progress_files = {}
        self.message = ""
        self.backups = []

class BackupSettings():
    def __init__(self, id: str, name: str,  repository_password: str, remote: ResticRemote):
        self.id = id
        self.name = name
        self.repository_password = repository_password
        self.remote = remote

class BackupConfig():
    def __init__(self, settings: BackupSettings, status: BackupStatus):
        self.settings = settings
        self.status = status 
    
class BackupStore():
    backup_configs = []

    def upsert_backup_config(self, backup_config: BackupConfig):
        for i, b in enumerate(self.backup_configs):
            if b.settings.id == backup_config.settings.id:
                status = self.backup_configs[i].status
                backup_config.status = status
                self.backup_configs[i] = backup_config
                return
        self.backup_configs.append(backup_config)
    
    def get_backup_configs(self) -> List[BackupConfig]:
        return self.backup_configs
    
    def get_backup_config(self, id: str) -> BackupConfig:
        for backup_config in self.backup_configs:
            if backup_config.settings.id == id:
                return backup_config
        return None
    
    def remove_backup_config(self, id: str) -> bool:
        for backup_config in self.backup_configs:
            if backup_config.settings.id == id:
                self.backup_configs.remove(backup_config)
                return True
        return False