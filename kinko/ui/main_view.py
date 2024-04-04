from gi.repository import Gtk, Adw, GObject
from datetime import datetime, timezone, timedelta
import timeago
import ipc
import ui.components
from ui.backup_list_entry import BackupListEntry
from event_monitors.system_status import NetworkStatus, PowerSaverStatus
from ui.template_loader import load_template

class MainView():
    def __init__(self, b, be, system_status, navigate_callback):
        self.backup_store = b
        self.backup_executor = be
        self.system_status = system_status
        self.navigate_callback = navigate_callback
    
    def tick(self):
        network_status = self.system_status.get_network_status()
        powersaver_status = self.system_status.get_power_saver_status()
        if network_status == NetworkStatus.DISCONNECTED:
            self.paused_banner.set_revealed(True)
            self.paused_banner.set_title("Backups are paused due to no network connection")
        elif network_status == NetworkStatus.METERED:
            self.paused_banner.set_revealed(True)
            self.paused_banner.set_title("Backups are paused due to metered network connection")
        elif powersaver_status == PowerSaverStatus.Enabled:
            self.paused_banner.set_revealed(True)
            self.paused_banner.set_title("Backups are paused due to power saver mode")
        else:
            self.paused_banner.set_revealed(False)

        self.render_list()
        return True

    def load(self):
        builder = load_template("main_view.ui")
        self.main_view = builder.get_object("view")
        self.content = builder.get_object("content")
        self.add_button = builder.get_object("add_button")
        self.add_button.connect("clicked", lambda _: self.navigate_callback("edit", None))
        self.paused_banner = builder.get_object("paused_banner")
        self.paused_banner.set_revealed(False)

        self.render_list()
        GObject.timeout_add(1000, lambda: self.tick())
        
        return self.main_view

    def navigate_to(self, param):
        GObject.timeout_add(100, lambda: self.render_list())
        return None

    def render_list(self):
        while self.content.get_first_child() is not None:
            self.content.get_first_child().destroyed = True
            self.content.remove(self.content.get_first_child())

        for backup_config in self.backup_store.get_backup_configs():
            self.backup_list_entry = BackupListEntry(self.backup_store, self.backup_executor, backup_config.settings.id, self.navigate_callback)
            self.content.append(self.backup_list_entry.load())