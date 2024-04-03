import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk, GObject
import sys
import ipc
import os
import time

from ui.main_view import MainView
from ui.edit_view import EditView

class KinkoApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        b = ipc.ProxyBackupStore()
        be = ipc.ProxyBackupExecutor()
        system_status = ipc.ProxySystemStatus()

        builder = Gtk.Builder()
        builder.add_from_file(".templates/kinko.ui")
        self.win = builder.get_object("window")
        self.stack = builder.get_object("main_stack")
        self.main_content = builder.get_object("main_content")
        self.edit_content = builder.get_object("edit_content")

        # builder = Gtk.Builder()
        # builder.add_from_file(".templates/edit_view.ui")
        # self.edit_view = builder.get_object("view")
        # self.edit_content.append(self.edit_view)

        self.edit_view = EditView(b, self.navigate, self.win)
        self.edit_content.append(self.edit_view.load())

        self.main_view = MainView(b, be, system_status, self.navigate)
        self.main_content.append(self.main_view.load())

        self.win.set_application(self)
        self.win.present()
        
        self.stack.set_visible_child_name("main_view")

        # d = Adw.AboutWindow(
        #     developer_name='quexten',
        #     developers=['quexten'],
        #     copyright='© 2023 Bernd Schoolmann',
        #     license_type=Gtk.License.MIT_X11,
        #     application_icon='com.quexten.Kinko',
        #     application_name='Kinko',
        #     version='dev',
        #     website='https://quexten.com',
        #     modal = True,
        #     transient_for=self.win)
        # d.set_visible(True)

    def navigate(self, view, param):
        if view == "main":
            self.stack.set_visible_child_name("main_view")
            self.main_view.navigate_to(param)
        elif view == "schedule":
            self.stack.set_visible_child(self.schedule_view_scrolled)
            self.schedule_view.navigate_to(param)
        elif view == "edit":
            self.stack.set_visible_child_name("edit_view")
            self.edit_view.navigate_to(param)
        elif view == "status":
            self.stack.set_visible_child(self.status_view_scrolled)
            self.status_view.navigate_to(param)
        elif view == "history":
            self.stack.set_visible_child(self.history_view_scrolled)
            self.history_view.navigate_to(param)
        elif view == "status":
            print("status")
        elif view == "restore":
            self.stack.set_visible_child(self.restore_view_scrolled)
            self.restore_view.navigate_to(param)
        else:
            raise Exception("Unknown view")

def load_css():
    isflatpak = os.path.exists("/.flatpak-info")
    pathprefix = "/app/bin/" if isflatpak else "./"
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(pathprefix+"style.css")
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

load_css()

app = KinkoApp(application_id="com.quexten.Kinko")
app.run(sys.argv)