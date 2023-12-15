#!/usr/bin/python
import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gui.edit_dialog import show_edit_backup_dialog
from gui.history_view import HistoryView
from gui.schedule_view import ScheduleView
from gui.status_view import StatusView
from gui.restore_view import RestoreView
from gi.repository import Gtk, Adw, Gdk, Graphene, Gsk, Gio, GLib, GObject
import backend.backup_store as backup_store
import backend.backup_executor as backup_executor
import event_monitors.power_monitor as power_monitor
import event_monitors.network_monitor as network_monitor
from gui.main_view import MainView
import backend.config as config
from backend import restic
import re

# load config
b = backup_store.BackupStore()
configs = config.read_all_configs()

for cfg in configs:
    b.add_backup_config(cfg)

# start event monitors & backup executor
be = backup_executor.BackupExecutor(b)
power_monitor.start_monitor(be)
network_monitor.start_monitor(be)

# gui
class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.set_child(self.stack)
    
        self.main_view = MainView(b, self.navigate)
        self.main_view_scrolled = Gtk.ScrolledWindow()
        self.main_view_scrolled.set_vexpand(True)
        self.main_view_scrolled.set_hexpand(False)
        self.main_view_scrolled.set_child(self.main_view)
        self.stack.add_named(self.main_view_scrolled, "main")
        self.stack.set_visible_child(self.main_view)

        self.history_view = HistoryView(b, self.navigate)
        self.history_view_scrolled = Gtk.ScrolledWindow()
        self.history_view_scrolled.set_vexpand(True)
        self.history_view_scrolled.set_hexpand(False)
        self.history_view_scrolled.set_child(self.history_view)
        self.stack.add_named(self.history_view_scrolled, "history")

        self.schedule_view = ScheduleView(b, self.navigate)
        self.schedule_view_scrolled = Gtk.ScrolledWindow()
        self.schedule_view_scrolled.set_vexpand(True)
        self.schedule_view_scrolled.set_hexpand(False)
        self.schedule_view_scrolled.set_child(self.schedule_view)
        self.stack.add_named(self.schedule_view_scrolled, "schedule")

        self.status_view = StatusView(b, be, self.navigate)
        self.status_view_scrolled = Gtk.ScrolledWindow()
        self.status_view_scrolled.set_vexpand(True)
        self.status_view_scrolled.set_hexpand(False)
        self.status_view_scrolled.set_child(self.status_view)
        self.stack.add_named(self.status_view_scrolled, "status")

        self.restore_view = RestoreView(b, be, self.navigate)
        self.restore_view_scrolled = Gtk.ScrolledWindow()
        self.restore_view_scrolled.set_vexpand(True)
        self.restore_view_scrolled.set_hexpand(False)
        self.restore_view_scrolled.set_child(self.restore_view)
        self.stack.add_named(self.restore_view_scrolled, "restore")

        self.set_default_size(700, 700)
        self.set_title("Resticat")
        self.navigate("main", None)

    def navigate(self, view, param):
        if view == "main":
            self.stack.set_visible_child(self.main_view_scrolled)
            self.main_view.navigate_to(param, self)
        elif view == "schedule":
            self.stack.set_visible_child(self.schedule_view_scrolled)
            self.schedule_view.navigate_to(param, self)
        elif view == "edit":
            show_edit_backup_dialog(self, b, param)
        elif view == "status":
            self.stack.set_visible_child(self.status_view_scrolled)
            self.status_view.navigate_to(param, self)
        elif view == "history":
            self.stack.set_visible_child(self.history_view_scrolled)
            self.history_view.navigate_to(param, self)
        elif view == "status":
            print("status")
        elif view == "restore":
            self.stack.set_visible_child(self.restore_view_scrolled)
            self.restore_view.navigate_to(param, self)
        else:
            raise Exception("Unknown view")
class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        if hasattr(self, "win") is False:
            app.hold()
            self.win = MainWindow(application=app)
            self.win.set_hide_on_close(True)
        
        self.win.present()

app = MyApp(application_id="com.quexten.Resticat")
app.run(sys.argv)