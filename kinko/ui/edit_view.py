from gi.repository import Gtk, Adw, Gio, GLib
import backend.config as config
import backend.backup_store as backup_store
from backend import restic, rclone, remotes
import uuid
import time

class EditView(Gtk.Box):
    def __init__(self, backup_store, navigate, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_store = backup_store
        self.navigate_callback = navigate
        self.window = window
        self.rclone_config = ""
        
    def load(self):
        builder = Gtk.Builder()
        builder.add_from_file(".templates/edit_view.ui")
        self.edit_view = builder.get_object("view")
        self.content = builder.get_object("content")
        self.back_button = builder.get_object("back_button")
        self.back_button.connect("clicked", lambda _: self.navigate_callback("main", None))
        self.id_row = builder.get_object("id_row")
        self.name_row = builder.get_object("name_row")
        self.rclone_path_row = builder.get_object("rclone_path_row")
        self.password_row = builder.get_object("password_row")
        self.rclone_button = builder.get_object("rclone_row")
        self.rclone_button.connect("activated", lambda _: self.edit_rclone())
        self.save_button = builder.get_object("save_button")
        self.save_button.connect("clicked", lambda _: self.save())
        self.remove_button = builder.get_object("remove_button")
        self.remove_button.connect("clicked", lambda _: self.remove())
        
        return self.edit_view

    def navigate_to(self, backup_id):
        if backup_id == None:
            self.id_row.set_subtitle(str(uuid.uuid4()))
            self.name_row.set_text("")
            self.rclone_path_row.set_text("")
            self.password_row.set_text("")
            self.rclone_config = ""
            # disable
            self.save_button.set_sensitive(True)
            self.password_row.set_sensitive(True)
            self.name_row.set_sensitive(True)
            self.rclone_path_row.set_sensitive(True)
            self.rclone_button.set_sensitive(True)
            self.remove_button.set_sensitive(False)
        else:
            self.id_row.set_subtitle(backup_id)
            conifg = self.backup_store.get_backup_config(backup_id)
            self.name_row.set_text(conifg.settings.name)
            self.rclone_path_row.set_text(conifg.settings.remote.path)
            self.password_row.set_text(conifg.settings.repository_password)
            self.rclone_config = conifg.settings.remote.rclone_config
            # enable
            self.save_button.set_sensitive(False)
            self.password_row.set_sensitive(False)
            self.name_row.set_sensitive(False)
            self.rclone_path_row.set_sensitive(False)
            self.rclone_button.set_sensitive(False)
            self.remove_button.set_sensitive(True)
    
    def _task_verify_rclone(self):
        start, end = self.config_textview.get_buffer().get_start_iter(), self.config_textview.get_buffer().get_end_iter()
        text = self.config_textview.get_buffer().get_text(start, end, True)
        res = rclone.test(self.config_textview.get_buffer().get_text(start, end, True))
        if res:
            print("rclone config is valid")
            self.dialog.close()
            self.rclone_config = text
        else:
            print("rclone config is invalid")

    def _verify_rclone(self):
        task = Gio.Task.new(None, None, None, None)
        task.run_in_thread(lambda *_: self._task_verify_rclone())

    def edit_rclone(self):
        builder = Gtk.Builder()
        builder.add_from_file(".templates/rclone_ui.ui")
        self.dialog = builder.get_object("dialog")
        self.config_textview = builder.get_object("config_textview")
        self.config_textview.get_buffer().set_text(self.rclone_config)

        self.dialog.present(self.window)
        self.cancel_button = builder.get_object("cancel_button")
        self.cancel_button.connect("clicked", lambda _: self.dialog.close())
        self.save_button = builder.get_object("save_button")
        self.save_button.connect("clicked", lambda _: self._verify_rclone())
    
    def create_backup_config(self):
        id = self.id_row.get_subtitle()
        name = self.name_row.get_text()
        path = self.rclone_path_row.get_text()
        password = self.password_row.get_text()
        remote = remotes.ResticRcloneRemote(self.rclone_config, path)
        return backup_store.BackupConfig(backup_store.BackupSettings(id, name, password, remote), backup_store.BackupStatus())

    def _task_create_repo(self):
        cfg = self.create_backup_config()
        res = restic.init(cfg.settings.remote, cfg.settings.repository_password)
        if res == "exists":
            print("error repo exists")
        print("repo created")
        self.backup_store.upsert_backup_config(cfg)
        self.navigate_callback("main", None)

    def save_result(self, res):
        if res == "ok":
            cfg = self.create_backup_config()
            self.backup_store.upsert_backup_config(cfg)
            self.navigate_callback("main", None)
        elif res == "norepo":
            dialog = Adw.MessageDialog.new(self.window, "No Repository Found")
            dialog.set_body("There was no repository found at the specified location. Do you want to create a new one?")
            dialog.set_title("No Repository Found")
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("ok", "Create")
            dialog.set_modal(True)
            dialog.set_visible(True)
            def create_repo(dialog, response_id):
                if response_id == "ok":
                    print("creating")
                    task = Gio.Task.new(None, None, None, None)
                    task.run_in_thread(lambda *_: self._task_create_repo())
                else:
                    print("cancel")
                    dialog.close()
            dialog.connect("response", create_repo)
        elif res == "password":
            print("wrong password")
            dialog = Adw.MessageDialog.new(None, "Wrong Password")
            dialog.set_body("The password you entered is wrong.")
            dialog.set_title("Wrong Password")
            dialog.add_response("ok", "Ok")
            dialog.set_modal(True)
            dialog.set_visible(True)
        else:
            print("unknown error")
            dialog = Adw.MessageDialog.new(None, "Unknown Error")
            dialog.set_body("An unknown error occured.")
            dialog.set_title("Unknown Error")
            dialog.add_response("ok", "Ok")
            dialog.set_modal(True)
            dialog.set_visible(True)

    def task_save(self):
        id = self.id_row.get_subtitle()
        name = self.name_row.get_text()
        path = self.rclone_path_row.get_text()
        password = self.password_row.get_text()
        remote = remotes.ResticRcloneRemote(self.rclone_config, path)
        res = restic.check_repo_status(remote, password)
        GLib.idle_add(self.save_result, res)

    def save(self):
        task = Gio.Task.new(None, None, None, None)
        task.run_in_thread(lambda *_: self.task_save())

    def remove(self):
        id = self.id_row.get_subtitle()
        self.backup_store.remove_backup_config(id)
        self.navigate_callback("main", None)