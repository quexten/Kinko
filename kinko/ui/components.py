from gi.repository import Gtk
from enum import Enum

class Status(Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    PRIMARY = "primary"

class StatusIcon(Gtk.Box):
    def __init__(self):
        super().__init__()
        self.icon_name = None
        self.status = None

    def set_icon(self, icon_name, status):
        if self.icon_name == icon_name and self.status == status:
            return

        self.icon_name = icon_name
        self.status = status

        while self.get_first_child() != None:
            self.remove(self.get_first_child())

        filename = "ui/status_icon/{}.ui".format(status)

        builder = Gtk.Builder()
        builder.add_from_file(filename)
        image = builder.get_object("image")
        image.set_from_icon_name(icon_name)