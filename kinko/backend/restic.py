import subprocess
import orjson as json
import os
from gi.repository import GLib
import time
import backend.remotes as remotes
from shutil import which

launch_command = []
restic_path = which("restic")
command_prefix = ["ionice", "-c", "3", "nice", "-n", "19"]

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
    result = subprocess.run(restic_cmd, env=env, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        if "already exists" in result.stderr:
            return "exists"
        raise Exception("Failed to initialize repository, err", result.stderr)

def check_repo_status(remote, password):
    remote.prepare_access()
    env, restic_cmd = get_restic_base(remote, password)
    restic_cmd = restic_cmd + ["snapshots"]
    print(restic_cmd)

    result = subprocess.run(restic_cmd, env=env, capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        return "ok"
    if result.returncode > 0:
        if "wrong password" in result.stderr:
            return "password"
        elif "Is there a repository" in result.stderr:
            return "norepo"
        else:
            print("unknown error", result.stderr)
            print(result.stdout)

def backup(remote, password, source, ignores, on_progress=None):
    remote.prepare_access()

    ignore_params = []
    ignores = ["\"{}\"".format(x) for x in ignores]
    if len(ignores) > 0:
        ignore_params = ("--exclude=" + " --exclude=".join(ignores)).split(" ")
    else:
        ignore_params = []

    repo, parameters = remote.get_restic_parameters()
    restic_cmd = launch_command + [restic_path, "-r", repo] + parameters + ["--json"]
    env = os.environ.copy()
    env["RESTIC_PASSWORD"] = password
    env["RESTIC_CACHE_DIR"] = GLib.get_user_cache_dir() + "/kinko"
    
    restic_cmd = command_prefix + restic_cmd + ["backup", "--compression", "auto", "--exclude-caches", "--tag", "com.quexten.kinko", "--one-file-system", "--exclude-larger-than", "250M"] + ignore_params + [source]
    cmdstring = " ".join(restic_cmd)
    process = subprocess.Popen(cmdstring, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, shell=True)
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

    for line in iter(process.stderr.readline, b""):
        print(line.decode("utf-8").strip())
    for line in iter(process.stdout.readline, b""):
        print(line.decode("utf-8").strip())
    
    # if error raise exception
    if process.returncode != 0:
        print(process.returncode)
        raise Exception("Failed to backup errcode" + str(process.returncode) + "+ err" + process.stderr)

    return result

def snapshots(remote, password):
    remote.prepare_access()
    env, restic_cmd = get_restic_base(remote, password)
    restic_cmd = restic_cmd + ["snapshots"]
    result = subprocess.run(restic_cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception("Failed to get snapshots, err", result.stderr)
    res = result.stdout
    return json.loads(res)