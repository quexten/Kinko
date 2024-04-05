from gi.repository import Gtk, Adw, Gio, GLib, GObject
import backend.config as config
import backend.backup_store as backup_store
from backend.backup_store import BackupStore
from backend.backup_executor import BackupExecutor
from backend import restic, rclone, remotes
import uuid
import time
from ui.template_loader import load_template
import timeago
from datetime import timedelta, datetime, timezone

class BackupView(Gtk.Box):
    def __init__(self, backup_store: BackupStore, backup_executor: BackupExecutor, navigate, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_store = backup_store
        self.backup_executor = backup_executor
        self.navigate_callback = navigate
        self.window = window
        self.backup_id = None

    def tick(self):
        # get status
        if self.backup_id is None:
            return True

        status = self.backup_store.get_backup_config(self.backup_id).status
        if status is None:
            return True
        
        print("tick", status.status_code, status.progress, status.message)
        
        if status.status_code == backup_store.BackupStatusCodes.Idle:
            next_backup_time = self.backup_executor.get_next_backup_time(self.backup_id)
            if next_backup_time == "now":
                self.time_label.set_text("Next backup now")
            elif next_backup_time == "metered":
                self.time_label.set_text("Next backup when not on metered network")
            elif next_backup_time == "powersaver":
                self.time_label.set_text("Next backup when power saver mode is disabled")
            else:
                self.time_label.set_text("Next backup in " + next_backup_time)
            
            self.status_label.set_text("Idle")
            self.log_scrolled_window.set_visible(False)
            self.progress_label.set_visible(False)
            self.progress_bar.set_visible(False)
            self.progress_bar.set_fraction(status.progress)
            self.log_scrolled_window.set_visible(False)
            self.log_textview.get_buffer().set_text(status.message)
            return True
        elif status.status_code == backup_store.BackupStatusCodes.Running:
            if status.seconds_elapsed is not None:
                if status.seconds_remaining is not None:
                    self.time_label.set_text("Elapsed: {}, Remaining: {}".format(format_seconds(status.seconds_elapsed), format_seconds(status.seconds_remaining)))
                else:
                    self.time_label.set_text("Elapsed: {}".format(format_seconds(status.seconds_elapsed)))
            self.log_scrolled_window.set_visible(True)
            self.progress_label.set_visible(True)
            self.progress_label.set_text("Progress: {}%".format(int(status.progress * 100)))
            self.progress_bar.set_fraction(status.progress)
            self.status_label.set_text("Running")
            self.progress_bar.set_visible(True)
            self.log_scrolled_window.set_visible(True)
            self.log_textview.get_buffer().set_text(status.message)
            return True

        return True
        
    def load(self):
        builder = load_template("backup_view.ui")
        self.backup_view = builder.get_object("view")
        self.content = builder.get_object("content")
        self.back_button = builder.get_object("back_button")
        self.back_button.connect("clicked", lambda _: self.navigate_callback("main", None))
        self.status_label = builder.get_object("status_label")
        self.time_label = builder.get_object("time_label")
        self.progress_label = builder.get_object("progress_label")
        self.progress_bar = builder.get_object("progress_bar")
        self.log_textview = builder.get_object("log_textview")
        self.log_scrolled_window = builder.get_object("log_scrolled_window")

        GObject.timeout_add(100, lambda: self.tick())
        
        return self.backup_view

    def navigate_to(self, backup_id):
        self.backup_id = backup_id
        pass

def format_seconds(seconds):
    if seconds < 60:
        return "{} seconds".format(seconds)
    if seconds < 60 * 60:
        return "{} minutes".format(seconds // 60)
    return "{} hours".format(seconds // 60 // 60)