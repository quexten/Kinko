import subprocess
import orjson as json
import os
from gi.repository import GLib
import time

launch_command = "ionice -c2 nice -n19"
restic_path = "/usr/bin/restic"
# if not exists change to /app/bin/restic
if not os.path.exists(restic_path):
    restic_path = "/app/bin/restic"

def init(repository, access_key_id, secret_access_key, password):
    restic_cmd = f"{launch_command} {restic_path} init --json -r {repository}"
    env = os.environ.copy()
    env["RESTIC_PASSWORD"] = password
    env["AWS_ACCESS_KEY_ID"] = access_key_id
    env["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    result = subprocess.run(restic_cmd.split(), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("Failed to initialize repository, err", result.stderr)

def check_repo_status(repository, access_key_id, secret_access_key, password):
    restic_cmd = f"{launch_command} {restic_path} snapshots --json -r {repository}"
    env = os.environ.copy()
    env["RESTIC_CACHE_DIR"] = GLib.get_user_cache_dir() + "/resticat"
    env["RESTIC_PASSWORD"] = password
    env["AWS_ACCESS_KEY_ID"] = access_key_id
    env["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    result = subprocess.run(restic_cmd.split(), env=env, capture_output=True, text=True)
    if result.returncode == 0:
        return "ok"
    if result.returncode > 0:
        if "wrong password" in result.stderr:
            return "password"
        elif "Is there a repository" in result.stderr:
            return "norepo"
        else:
            print("unknown error", result.stderr)

def backup(repository, access_key_id, secret_access_key, password, source, ignores, on_progress=None):
    ignores_string = " --exclude " + " --exclude ".join(ignores)
    restic_cmd = f'{launch_command} {restic_path}  -r {repository} backup --compression auto --exclude-caches --tag com.quexten.resticat --one-file-system --exclude-larger-than 128M ' + ignores_string + f' --json {source}'
    env = os.environ.copy()
    env["RESTIC_CACHE_DIR"] = GLib.get_user_cache_dir() + "/resticat"
    env["RESTIC_PASSWORD"] = password
    env["AWS_ACCESS_KEY_ID"] = access_key_id
    env["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    process = subprocess.Popen(restic_cmd.split(), stdout=subprocess.PIPE, env=env)

    result = None

    for line in iter(process.stdout.readline, b""):
        output = line.decode("utf-8")
        try:
            status = json.loads(output)
            if on_progress is not None:
                if status.get("message_type") == "summary":
                    result = status
                else:
                    on_progress(status)
            else:
                print(output.strip())
        except json.JSONDecodeError:
            print(output.strip())
    process.wait()
    
    # if error raise exception
    if process.returncode != 0:
        print(process.returncode)
        raise Exception("Failed to backup errcode" + str(process.returncode) + "+ err" + process.stderr)

    return result

def snapshots(repository, access_key_id, secret_access_key, password):
    restic_cmd = f"{launch_command} {restic_path} snapshots --json -r {repository}"
    env = os.environ.copy()
    env["RESTIC_CACHE_DIR"] = GLib.get_user_cache_dir() + "/resticat"
    env["RESTIC_PASSWORD"] = password
    env["AWS_ACCESS_KEY_ID"] = access_key_id
    env["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    result = subprocess.run(restic_cmd.split(), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("Failed to get snapshots, err", result.stderr)
    return json.loads(result.stdout)

def files_for_snapshot(repository, access_key_id, secret_access_key, password, snapshot_id):
    restic_cmd = f"{launch_command} {restic_path} ls --json -r {repository} {snapshot_id}"
    env = os.environ.copy()
    env["CACHE_DIR"] = GLib.get_user_cache_dir() + "/resticat"
    env["RESTIC_PASSWORD"] = password
    env["AWS_ACCESS_KEY_ID"] = access_key_id
    env["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    result = subprocess.run(restic_cmd.split(), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("Failed to get files for snapshot, err", result.stderr)
    
    results = []
    for line in result.stdout.split("\n")[1:]:
        try:
            res = json.loads(line)
            results.append(res)
        except:
            pass
    return results    

def stats(repository, access_key_id, secret_access_key, password):
    restic_cmd = launch_command + f"restic stats --json -r {repository}"
    env = os.environ.copy()
    env["CACHE_DIR"] = GLib.get_user_cache_dir() + "/resticat"
    env["RESTIC_PASSWORD"] = password
    env["AWS_ACCESS_KEY_ID"] = access_key_id
    env["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    result = subprocess.run(restic_cmd.split(), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("Failed to get stats, err", result.stderr)
    return json.loads(result.stdout)

def forget(repository, access_key_id, secret_access_key, password, keep_hourly, keep_daily, keep_weekly, keep_monthly, keep_yearly):
    restic_cmd = f"{launch_command} {restic_path} forget -r {repository} --tag com.quexten.resticat --keep-hourly {keep_hourly} --keep-daily {keep_daily} --keep-weekly {keep_weekly} --keep-monthly {keep_monthly} --keep-yearly {keep_yearly}"
    env = os.environ.copy()
    env["RESTIC_PASSWORD"] = password 
    env["AWS_ACCESS_KEY_ID"] = access_key_id
    env["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    result = subprocess.Popen(restic_cmd.split(), stdout=subprocess.PIPE, env=env)

    for line in iter(result.stdout.readline, b""):
        output = line.decode("utf-8")
        print(output.strip())
    
    result.wait()
    time.sleep(2)
    return result

def restore(repository, access_key_id, secret_access_key, password, snapshot_id, mountpoint, includes, exclude, destination, on_progress=None):
    files_string = "--include " + " --include ".join(includes)
    if len(includes) == 0:
        files_string = ""
    restic_cmd = f"{launch_command} {restic_path} restore --tag com.quexten.resticat -r {repository} {files_string} {snapshot_id}:{mountpoint} --json --target {destination}"
    env = os.environ.copy()
    env["CACHE_DIR"] = GLib.get_user_cache_dir() + "/resticat"
    env["RESTIC_PASSWORD"] = password
    env["AWS_ACCESS_KEY_ID"] = access_key_id
    env["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    process = subprocess.Popen(restic_cmd.split(), stdout=subprocess.PIPE, env=env)

    result = None

    for line in iter(process.stdout.readline, b""):
        output = line.decode("utf-8")
        try:
            status = json.loads(output)
            if on_progress is not None:
                if status.get("message_type") == "summary":
                    result = status
                else:
                    on_progress(status)
            else:
                print(output.strip())
        except json.JSONDecodeError:
            print(output.strip())
    process.wait()
    
    # if error raise exception
    if process.returncode != 0:
        print(process.returncode)
        raise Exception("Failed to restore errcode" + str(process.returncode) + "+ err" + process.stderr)

    return result

def prune(repository, access_key_id, secret_access_key, password):
    restic_cmd = launch_command + f"restic prune -r {repository}"
    env = os.environ.copy()
    env["CACHE_DIR"] = GLib.get_user_cache_dir() + "/resticat"
    env["RESTIC_PASSWORD"] = password
    env["AWS_ACCESS_KEY_ID"] = access_key_id
    env["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    result = subprocess.run(restic_cmd.split(), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("Failed to prune repository, err", result.stderr)
    return result.stdout

def check(repository, access_key_id, secret_access_key, password):
    restic_cmd = f"{launch_command} {restic_path} check --json -r {repository}"
    env = os.environ.copy()
    env["CACHE_DIR"] = GLib.get_user_cache_dir() + "/resticat"
    env["RESTIC_PASSWORD"] = password
    env["AWS_ACCESS_KEY_ID"] = access_key_id
    env["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    result = subprocess.run(restic_cmd.split(), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("Failed to check repository, err", result.stderr)
    return result.stdout
