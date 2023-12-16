import json
import backend.backup_store as backup_store
import secretstorage
from pathlib import Path
import secrets
from gi.repository import Gtk, Adw, Gdk, Graphene, Gsk, Gio, GLib, GObject
from Crypto.Cipher import ChaCha20_Poly1305
from base64 import b64encode, b64decode

def config_to_json(config):
    config_dict = {}
    config_dict["settings"] = {
        "id": config.settings.id,
        "name": config.settings.name,
        "aws_s3_secret_key": config.settings.aws_s3_secret_key,
        "aws_s3_access_key": config.settings.aws_s3_access_key,
        "aws_s3_repository": config.settings.aws_s3_repository,
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
        "on_network": config.schedule.on_network,
        "on_ac": config.schedule.on_ac,

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
    Path(GLib.get_user_data_dir()+"/resticat/").mkdir(parents=True, exist_ok=True)

    encrypted_configs = []
    for backup_config in backup_store.get_backup_configs():
        config = config_to_json(backup_config)
        encrypted_config = encrypt_string(config, get_application_encryption_key())
        encrypted_configs.append(encrypted_config)
    encrypted_configs = "\n".join(encrypted_configs)
    with open(GLib.get_user_data_dir() + "/resticat/config", "w") as f:
        f.write(encrypted_configs)

def read_all_configs():
    try:
        with open(GLib.get_user_data_dir() + "/resticat/config", "r") as f:
            encrypted_configs = f.read()
        encrypted_configs = encrypted_configs.split("\n")
        configs = []
        for encrypted_config in encrypted_configs:
            try:
                config = decrypt_string(encrypted_config, get_application_encryption_key())
                configs.append(json_to_config(config))
            except:
                pass
        return configs
    except Exception as ex:
        return []
 
def json_to_config(json_cfg):
    config_dict = json.loads(json_cfg)
    backup_settings = backup_store.BackupSettings(
        config_dict["settings"]["id"],
        config_dict["settings"]["name"],
        config_dict["settings"]["aws_s3_secret_key"],
        config_dict["settings"]["aws_s3_access_key"],
        config_dict["settings"]["aws_s3_repository"],
        config_dict["settings"]["repository_password"],
        config_dict["settings"]["sources"],
    )
    backup_schedule = backup_store.BackupSchedule(
    )
    backup_schedule.allow_on_metered = config_dict["schedule"]["allow_on_metered"]
    backup_schedule.on_network = config_dict["schedule"]["on_network"]
    backup_schedule.on_ac = config_dict["schedule"]["on_ac"]
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

def encrypt_string(content, key):
    # chacha20-poly1305
    cipher = ChaCha20_Poly1305.new(key=key)
    cipher.update(b"header")
    ciphertext, tag = cipher.encrypt_and_digest(content.encode("utf-8"))
    nonce = b64encode(cipher.nonce).decode("utf-8")
    ciphertext = b64encode(ciphertext).decode("utf-8")
    tag = b64encode(tag).decode("utf-8")
    res = nonce + "." + ciphertext + "." + tag
    return res

def decrypt_string(string, key):
    # chacha20-poly1305
    nonce, ciphertext, tag = string.split(".")
    nonce = b64decode(nonce)
    ciphertext = b64decode(ciphertext)
    tag = b64decode(tag)
    cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    cipher.update(b"header")
    return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")

def get_application_encryption_key():
    connection = secretstorage.dbus_init()
    collection = secretstorage.get_default_collection(connection)
    if collection.is_locked():
        collection.unlock()
    for item in collection.search_items({"application": "com.quexten.Resticat"}):
        return item.get_secret()
    key = secrets.token_bytes(32)
    collection.create_item("application_key", {"application": "com.quexten.Resticat"}, key, replace=True)
    return key