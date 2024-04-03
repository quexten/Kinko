import subprocess
import orjson as json
import os
from gi.repository import GLib
import time
from shutil import which

rclone_path = which("rclone")

def test(config_string):
    # write config
    with open("/tmp/rclone.conf", "w") as f:
        f.write("[remote]\n")
        f.write(config_string)
    rclone_cmd = f"{rclone_path} --low-level-retries=0 --config /tmp/rclone.conf lsd remote:"
    result = subprocess.run(rclone_cmd.split(), capture_output=True, text=True)
    if result.returncode != 0:
        return False
    return True
