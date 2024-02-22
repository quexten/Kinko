import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gui.edit_view import EditView
from gui.history_view import HistoryView
from gui.schedule_view import BackupConfigView
from gui.status_view import StatusView
from gui.restore_view import RestoreView
from gui.edit_view import EditView
from gi.repository import Gtk, Adw, Gdk
import sys
from gui.main_view import MainView
import ipc
import os
import time

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.set_child(self.stack)
    
        b = ipc.ProxyBackupStore()
        be = ipc.ProxyBackupExecutor()
        self.main_view = MainView(b, be, self.navigate)
        self.main_view_scrolled = Gtk.ScrolledWindow()
        self.main_view_scrolled.set_vexpand(True)
        self.main_view_scrolled.set_hexpand(False)
        self.main_view_scrolled.set_child(self.main_view)
        self.stack.add_named(self.main_view_scrolled, "main")

        self.history_view = HistoryView(b, self.navigate)
        self.history_view_scrolled = Gtk.ScrolledWindow()
        self.history_view_scrolled.set_vexpand(True)
        self.history_view_scrolled.set_hexpand(False)
        self.history_view_scrolled.set_child(self.history_view)
        self.stack.add_named(self.history_view_scrolled, "history")

        self.schedule_view = BackupConfigView(b, self.navigate)
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

        self.edit_view = EditView(b, self.navigate)
        self.edit_view_scrolled = Gtk.ScrolledWindow()
        self.edit_view_scrolled.set_vexpand(True)
        self.edit_view_scrolled.set_hexpand(False)
        self.edit_view_scrolled.set_child(self.edit_view)
        self.stack.add_named(self.edit_view_scrolled, "edit")

        self.set_default_size(700, 700)
        self.set_title("Kinko")

        self.navigate("main", None)

    
    # def show_open_dialog(self, button):
        # self.open_dialog.show()
        # print("show")

    # def open_response(self, dialog, response):
        # print("response")
    #     if response == Gtk.ResponseType.ACCEPT:
    #         file = dialog.get_file()
    #         filename = file.get_path()
    #         print(filename)  # Here you could handle opening or saving the file

    def navigate(self, view, param):
        if view == "main":
            self.stack.set_visible_child(self.main_view_scrolled)
            self.main_view.navigate_to(param, self)
        elif view == "schedule":
            self.stack.set_visible_child(self.schedule_view_scrolled)
            self.schedule_view.navigate_to(param, self)
        elif view == "edit":
            self.stack.set_visible_child(self.edit_view_scrolled)
            self.edit_view.navigate_to(param, self)
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
        self.win = MainWindow(application=app)
        self.win.present()

isflatpak = os.path.exists("/.flatpak-info")
pathprefix = "/app/bin/" if isflatpak else "./"
print("path", pathprefix+"style.css")
css_provider = Gtk.CssProvider()
css_provider.load_from_path(pathprefix+"style.css")
Gtk.StyleContext.add_provider_for_display(
    Gdk.Display.get_default(),
    css_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

app = MyApp(application_id="com.quexten.Kinko")
app.run(sys.argv)

time.sleep(10)