from abc import ABC, abstractmethod
import backend.rclone
from shutil import which
from subprocess import Popen
import time

rclone_path = which("rclone")

class ResticRemote(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def test(self):
        pass

    @abstractmethod
    def prepare_access(self):
        pass

    @abstractmethod
    def get_restic_parameters(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass
    
class ResticRcloneRemote(ResticRemote):
    def __init__(self, rclone_config, path):
        super().__init__("rclone")
        self.rclone_config = rclone_config
        self.path = path
        self.process = None

    def test(self):
        return backend.rclone.test(self.rclone_config)

    def prepare_access(self):
        with open("/tmp/rclone-kinko.conf", "w") as f:
            f.write("[remote]\n")
            f.write(self.rclone_config)
            print("wrote rclone config to /tmp/rclone-kinko.conf")

    def get_restic_parameters(self):
        return "rest:http://localhost:8080/"+self.path, []

    def start(self):
        self.prepare_access()
        if self.process is not None:
            return
        self.process = Popen("/app/bin/rclone serve restic --dscp CS1 --config /tmp/rclone-kinko.conf remote:", shell=True)
    
    def stop(self):
        self.process.terminate()
        self.process.wait()
    
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["process"]
        return state
