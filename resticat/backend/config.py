import json
import backend.backup_store as backup_store
from pathlib import Path
from gi.repository import GLib
from base64 import b64encode, b64decode

def config_to_json(config):
    config_dict = {}
    config_dict["settings"] = {
        "id": config.settings.id,
        "name": config.settings.name,
        "s3_secret_key": config.settings.s3_secret_key,
        "s3_access_key": config.settings.s3_access_key,
        "s3_repository": config.settings.s3_repository,
        "repository_password": config.settings.repository_password,
        "sources": config.settings.sources,
        "ignores_cache": config.settings.ignores_cache,
        "ignore_trash": config.settings.ignore_trash,
        "ignore_downloads": config.settings.ignore_downloads,
        "ignore_videos": config.settings.ignore_videos,
        "ignore_vms": config.settings.ignore_vms,
    }

    config_dict["schedule"] = {
        "allow_on_metered": config.schedule.allow_on_metered,
        "allow_on_battery": config.schedule.allow_on_battery,
        "allow_on_powersaver": config.schedule.allow_on_powersaver,

        "backup_schedule_enabled": config.schedule.backup_schedule_enabled,
        "backup_schedule_frequency": config.schedule.backup_frequency,
        
        "cleanup_schedule_enabled": config.schedule.cleanup_schedule_enabled,
        "cleanup_schedule_frequency": config.schedule.cleanup_frequency,
        "cleanup_keep_hourly": config.schedule.cleanup_keep_hourly,
        "cleanup_keep_daily": config.schedule.cleanup_keep_daily,
        "cleanup_keep_weekly": config.schedule.cleanup_keep_weekly,
        "cleanup_keep_monthly": config.schedule.cleanup_keep_monthly,
        "cleanup_keep_yearly": config.schedule.cleanup_keep_yearly,
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
    print(GLib.get_user_config_dir() + "/kinko/config")
    try:
        with open(GLib.get_user_config_dir() + "/kinko/config", "r") as f:
            configs = f.read()
        configs = configs.split("\n")
        # from json
        configs = [json_to_config(config) for config in configs]
        return configs
    except Exception as ex:
        return []
 
def json_to_config(json_cfg):
    config_dict = json.loads(json_cfg)
    backup_settings = backup_store.BackupSettings(
        config_dict["settings"]["id"],
        config_dict["settings"]["name"],
        config_dict["settings"]["s3_secret_key"],
        config_dict["settings"]["s3_access_key"],
        config_dict["settings"]["s3_repository"],
        config_dict["settings"]["repository_password"],
        config_dict["settings"]["sources"],
    )
    backup_schedule = backup_store.BackupSchedule(
    )
    backup_schedule.allow_on_metered = config_dict["schedule"]["allow_on_metered"]
    backup_schedule.allow_on_battery = config_dict["schedule"]["allow_on_battery"] if "allow_on_battery" in config_dict["schedule"] else True
    backup_schedule.allow_on_powersaver = config_dict["schedule"]["allow_on_powersaver"] if "allow_on_powersaver" in config_dict["schedule"] else True
    backup_schedule.backup_schedule_enabled = config_dict["schedule"]["backup_schedule_enabled"]
    backup_schedule.backup_frequency = config_dict["schedule"]["backup_schedule_frequency"]
    backup_schedule.cleanup_schedule_enabled = config_dict["schedule"]["cleanup_schedule_enabled"]
    backup_schedule.cleanup_frequency = config_dict["schedule"]["cleanup_schedule_frequency"]
    backup_schedule.cleanup_keep_hourly = config_dict["schedule"]["cleanup_keep_hourly"]
    backup_schedule.cleanup_keep_daily = config_dict["schedule"]["cleanup_keep_daily"]
    backup_schedule.cleanup_keep_weekly = config_dict["schedule"]["cleanup_keep_weekly"]
    backup_schedule.cleanup_keep_monthly = config_dict["schedule"]["cleanup_keep_monthly"]
    backup_schedule.cleanup_keep_yearly = config_dict["schedule"]["cleanup_keep_yearly"]

    backup_config = backup_store.BackupConfig(
        backup_settings,
        backup_store.BackupStatus(),
        backup_schedule,
    )
    return backup_config 
