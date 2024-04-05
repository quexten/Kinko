from gi.repository import Gtk, Adw, GObject
from datetime import datetime, timezone, timedelta
import timeago
import ipc
import ui.components
from backend.backup_store import BackupStatusCodes
from ui.template_loader import load_template
class BackupListEntry(Gtk.Box):
    def __init__(self, backup_store, backup_executor, id, navigate_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_store = backup_store
        self.backup_executor = backup_executor
        self.id = id
        self.navigate_callback = navigate_callback
    
    def tick(self):
        self.render()
        if self.entry is not None and "destroyed" in dir(self.entry) and self.entry.destroyed:
            return False
        return True

    def load(self):
        builder = load_template("backup_list_entry.ui")

        self.entry = builder.get_object("listbox")
        self.title_row = builder.get_object("title_row")
        self.title_row.connect("activated", lambda _: self.navigate_callback("edit", self.id))
        self.status_row = builder.get_object("status_row")
        self.status_row.connect("activated", lambda _: self.navigate_callback("backup", self.id))

        self.render()
        GObject.timeout_add(1000, lambda: self.tick())
        return self.entry

    def render(self):
        config = self.backup_store.get_backup_config(self.id)
        # check if removed
        if config.status.status_code == BackupStatusCodes.Idle:
            self.status_row.set_title("Idle")
            next_backup_time = self.backup_executor.get_next_backup_time(self.id)
            if next_backup_time == "now":
                self.status_row.set_subtitle("Next backup now")
            elif next_backup_time == "metered":
                self.status_row.set_subtitle("Next backup when not on metered network")
            elif next_backup_time == "powersaver":
                self.status_row.set_subtitle("Next backup when power saver mode is disabled")
            else:
                self.status_row.set_subtitle("Next backup in " + next_backup_time)
        elif config.status.status_code == BackupStatusCodes.Running:
            self.status_row.set_title("Running")
            self.status_row.set_subtitle("Backing up...")
        name = self.backup_store.get_backup_config(self.id).settings.name
        self.title_row.set_title(name)
        self.title_row.set_subtitle("rclone remote")
    

