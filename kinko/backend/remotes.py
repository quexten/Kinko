from abc import ABC, abstractmethod
import backend.rclone
from shutil import which

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
    
class ResticRcloneRemote(ResticRemote):
    def __init__(self, rclone_config, path):
        super().__init__("rclone")
        self.rclone_config = rclone_config
        self.path = path

    def test(self):
        return backend.rclone.test(self.rclone_config)

    def prepare_access(self):
        with open("/tmp/rclone-kinko.conf", "w") as f:
            f.write("[remote]\n")
            f.write(self.rclone_config)
            print("wrote rclone config to /tmp/rclone-kinko.conf")

    def get_restic_parameters(self):
        return "rclone:remote:/"+self.path, ["-o", 'rclone.args=serve restic --stdio --dscp CS1 --config /tmp/rclone-kinko.conf']