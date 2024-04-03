import subprocess
import orjson as json
import os
from gi.repository import GLib
import time
import backend.remotes as remotes
from shutil import which

launch_command = ["ionice", "-c2", "nice", "-n19"]
restic_path = which("restic")

def get_restic_base(remote, password):
    repo, parameters = remote.get_restic_parameters()
    env = os.environ.copy()
    env["RESTIC_PASSWORD"] = password
    env["RESTIC_CACHE_DIR"] = GLib.get_user_cache_dir() + "/kinko"
    return env, launch_command + [restic_path, "-r", repo] + parameters + ["--json"]

def init(remote, password):
    remote.prepare_access()
    env, restic_cmd = get_restic_base(remote, password)
    restic_cmd = restic_cmd + ["init"]
    print(restic_cmd)
    result = subprocess.run(restic_cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        if "already exists" in result.stderr:
            return "exists"
        raise Exception("Failed to initialize repository, err", result.stderr)

def check_repo_status(remote, password):
    remote.prepare_access()
    env, restic_cmd = get_restic_base(remote, password)
    restic_cmd = restic_cmd + ["snapshots"]
    print(restic_cmd)

    result = subprocess.run(restic_cmd, env=env, capture_output=True, text=True)
    if result.returncode == 0:
        return "ok"
    if result.returncode > 0:
        if "wrong password" in result.stderr:
            return "password"
        elif "Is there a repository" in result.stderr:
            return "norepo"
        else:
            print("unknown error", result.stderr)

def backup(remote, password, source, ignores, on_progress=None):
    remote.prepare_access()
    env, restic_cmd = get_restic_base(remote, password)
    repository, parameters = remote.get_restic_parameters()

    ignore_params = []
    print(ignores)
    if len(ignores) > 0:
        ignore_params = ("--exclude=" + " --exclude=".join(ignores)).split(" ")
    else:
        ignore_params = []

    restic_cmd = restic_cmd + ["backup", "--compression", "auto", "--exclude-caches", "--tag", "com.quexten.kinko", "--one-file-system", "--exclude-larger-than", "250M"] + ignore_params + parameters + ["--json", source]
    print(restic_cmd)
    process = subprocess.Popen(restic_cmd, stdout=subprocess.PIPE, env=env)

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
                print("no on progress handler", output.strip())
        except json.JSONDecodeError:
            print(output.strip())
    process.wait()
    
    # if error raise exception
    if process.returncode != 0:
        print(process.returncode)
        raise Exception("Failed to backup errcode" + str(process.returncode) + "+ err" + process.stderr)

    return result

def snapshots(remote, password):
    remote.prepare_access()
    env, restic_cmd = get_restic_base(remote, password)
    restic_cmd = restic_cmd + ["snapshots"]
    print(restic_cmd)
    result = subprocess.run(restic_cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("Failed to get snapshots, err", result.stderr)
    return json.loads(result.stdout)