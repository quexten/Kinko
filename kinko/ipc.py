import os
import socket
import pickle
import time
import backend.config as config

is_flatpak = os.path.exists("/.flatpak-info")
socket_path = "/tmp/kinko.sock"
if is_flatpak:
    socket_path = os.path.expanduser("~") + "/.kinko.sock"

class ProxyBackupStore():
    def __init__(self):
        pass

    def get_backup_configs(self):
        return send_command("store.get_backup_configs", None)
    def get_backup_config(self, id):
        return send_command("store.get_backup_config", id)
    def upsert_backup_config(self, backup_config):
        return send_command("store.upsert_backup_config", backup_config)
    def remove_backup_config(self, id):
        return send_command("store.remove_backup_config", id)

class ProxyBackupExecutor():
    def __init__(self):
        pass

    def refresh_backups(self):
        return send_command("executor.refresh_backups", None)

    def restore_now(self, backup_config_id, snapshot_id, restore_path):
        return send_command("executor.restore_now", (backup_config_id, snapshot_id, restore_path))

    def backup_now(self, backup_config_id):
        return send_command("executor.backup_now", backup_config_id)
    
    def get_backups(self, id):
        return send_command("executor.get_backups", id)
    
    def clean_now(self, backup_config_id):
        return send_command("executor.clean_now", backup_config_id)

    def get_next_backup_time(self, backup_config_id):
        return send_command("executor.get_next_backup_time", backup_config_id)
    
class ProxySystemStatus():
    def __init__(self):
        pass

    def get_network_status(self):
        return send_command("system_status.get_network_status", None)
    
    def get_power_saver_status(self):
        return send_command("system_status.get_power_saver_status", None)

def send_command(action, data):
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    conn.connect(socket_path)
    packet = {}
    packet["action"] = action
    packet["data"] = data
    packet = pickle.dumps(packet, protocol=pickle.HIGHEST_PROTOCOL)
    length_bytes = len(packet).to_bytes(4, byteorder="big")
    conn.sendall(length_bytes + packet)
    response_bytes = conn.recv(4)
    response_length = int.from_bytes(response_bytes, byteorder="big")
    response = conn.recv(response_length)

    try:
        response = pickle.loads(response)
        return response
    except:
        time.sleep(0.05)
        # print("ipc error, retrying...")
        return send_command(action, data)

def handle_command(action, data, backup_store, backup_executor):
    response = {}
    if action == "store.get_backup_configs":
        response = backup_store.get_backup_configs()
    elif action == "store.get_backup_config":
        response = backup_store.get_backup_config(data)
    elif action == "store.upsert_backup_config":
        backup_store.upsert_backup_config(data)
        config.save_all_configs(backup_store)
        response = None
    elif action == "store.remove_backup_config":
        backup_store.remove_backup_config(data)
        response = None
    elif action == "executor.refresh_backups":
        backup_executor.refresh_backups()
        response = None
    elif action == "executor.restore_now":
        backup_executor.restore_now(data[0], data[1], data[2])
        response = None
    elif action == "executor.backup_now":
        backup_executor.backup_now(data)
        response = None
    elif action == "executor.get_backups":
        response = backup_executor.get_backups(data)
    elif action == "executor.clean_now":
        backup_executor.clean_now(data)
        response = None
    elif action == "executor.get_next_backup_time":
        response = backup_executor.get_next_backup_time(data)
    elif action == "system_status.get_network_status":
        response = backup_executor.system_status.get_network_status()
    elif action == "system_status.get_power_saver_status":
        response = backup_executor.system_status.get_power_saver_status()
    return response

def daemonize(backup_store, backup_executor):
    if os.path.exists(socket_path):
        os.remove(socket_path)
    print("Starting daemon...", socket_path)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(socket_path)

    while True:
        try:
            server.listen(1)
            conn, addr = server.accept()
            packet_length_bytes = conn.recv(4)
            packet_length = int.from_bytes(packet_length_bytes, byteorder="big")
            packet = conn.recv(packet_length)
            packet = pickle.loads(packet)
            response = handle_command(packet["action"], packet["data"], backup_store, backup_executor)
            response = pickle.dumps(response, protocol=pickle.HIGHEST_PROTOCOL)
            response_length = len(response).to_bytes(4, byteorder="big")
            conn.sendall(response_length + response)
            conn.close()
        except Exception as e:
            print(e)
            pass