import json
import backend.backup_store as backup_store
from pathlib import Path
from gi.repository import GLib
from base64 import b64encode, b64decode
from backend import remotes

def config_to_json(config):
    config_dict = {}
    config_dict["settings"] = {
        "id": config.settings.id,
        "name": config.settings.name,
        "remote": {
            "name": config.settings.remote.name,
            "rclone_config": config.settings.remote.rclone_config,  
            "path": config.settings.remote.path,
        },
        "repository_password": config.settings.repository_password,
    }

    return json.dumps(config_dict)

def save_all_configs(backup_store):
    # if config dir does not exist, create
    Path(GLib.get_user_config_dir()+"/kinko/").mkdir(parents=True, exist_ok=True)
    print("saving configs to", GLib.get_user_config_dir() + "/kinko/config")
    
    configs = []
    for backup_config in backup_store.get_backup_configs():
        config = config_to_json(backup_config)
        configs.append(config)
    print("saving", len(configs), "configs")
    configs = "\n".join(configs)
    with open(GLib.get_user_config_dir() + "/kinko/config", "w") as f:
        f.write(configs)

def read_all_configs():
    print("reading all configs from", GLib.get_user_config_dir() + "/kinko/config")
    try:
        with open(GLib.get_user_config_dir() + "/kinko/config", "r") as f:
            configs = f.read()

        configs = configs.split("\n")
        configs = [config for config in configs if config != ""]
        configs = [json_to_config(config) for config in configs]

        print("loaded", len(configs), "configs")

        return configs
    except Exception as ex:
        print("not loaded", ex)
        return []
 
def json_to_config(json_cfg):
    config_dict = json.loads(json_cfg)
    remote = remotes.ResticRcloneRemote(config_dict["settings"]["remote"]["rclone_config"], config_dict["settings"]["remote"]["path"])
    remote.start()
    backup_settings = backup_store.BackupSettings(
        config_dict["settings"]["id"],
        config_dict["settings"]["name"],
        config_dict["settings"]["repository_password"],
        remote,
    )

    backup_config = backup_store.BackupConfig(
        backup_settings,
        backup_store.BackupStatus(),
    )
    return backup_config 
