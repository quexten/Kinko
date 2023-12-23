from gi.repository import Gtk, Adw
import backend.config as config
import backend.backup_store as backup_store
from backend import restic
import uuid

class EditView(Gtk.Box):
    def __init__(self, backup_store, navigate):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_store= backup_store
        self.navigate_callback = navigate
        
    def navigate_to(self, param, window):
        self.selected_id = param
        backup_id = param
        b_store = self.backup_store

        self.header = Gtk.HeaderBar()
        self.back_button = Gtk.Button(label="Back")
        def back_button_clicked(button):
            while self.get_first_child() is not None:
                self.remove(self.get_first_child())
            self.navigate_callback("main", None)
        self.back_button.connect("clicked", lambda _: back_button_clicked(self.back_button))
        self.header.pack_start(self.back_button)
        window.set_titlebar(self.header)
        
        self.add_backup_win_scroll = Gtk.ScrolledWindow()
        self.add_backup_win_scroll.set_vexpand(True)
        self.add_backup_win_scroll.set_hexpand(False)

        self.add_backup_win_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add_backup_win_content.set_margin_start(80)
        self.add_backup_win_content.set_margin_end(80)
        self.add_backup_win_content.set_margin_top(10)
        self.add_backup_win_scroll.set_child(self.add_backup_win_content)

        # general
        self.add_backup_win_general_box = Adw.PreferencesGroup()
        self.add_backup_win_general_box.set_margin_top(10)
        self.add_backup_win_general_box.set_title("General")
        self.add_backup_win_general_box.set_description("General settings")
        self.add_backup_win_content.append(self.add_backup_win_general_box)

        self.add_backup_win_id_row = Adw.ActionRow()
        self.add_backup_win_id_row.set_title("ID")
        # random uuid
        if backup_id is None:
            self.add_backup_win_id_row.set_subtitle(str(uuid.uuid4()))
        else:
            self.add_backup_win_id_row.set_subtitle(backup_id)
        self.add_backup_win_general_box.add(self.add_backup_win_id_row)

        self.add_backup_win_name_row = Adw.EntryRow()
        self.add_backup_win_name_row.set_title("Name")
        self.add_backup_win_name_row.set_text("Name")
        self.add_backup_win_general_box.add(self.add_backup_win_name_row)

        # aws
        self.add_backup_win_aws_box = Adw.PreferencesGroup()
        self.add_backup_win_aws_box.set_margin_top(10)
        self.add_backup_win_aws_box.set_title("AWS")
        self.add_backup_win_aws_box.set_description("AWS credentials")
        self.add_backup_win_content.append(self.add_backup_win_aws_box)

        self.add_backup_win_aws_secret_key_row = Adw.PasswordEntryRow()
        self.add_backup_win_aws_secret_key_row.set_title("AWS Secret Key")
        self.add_backup_win_aws_box.add(self.add_backup_win_aws_secret_key_row)

        self.add_backup_win_aws_access_key_row = Adw.PasswordEntryRow()
        self.add_backup_win_aws_access_key_row.set_title("AWS Access Key")
        self.add_backup_win_aws_box.add(self.add_backup_win_aws_access_key_row)

        self.add_backup_win_aws_repository_row = Adw.EntryRow()
        self.add_backup_win_aws_repository_row.set_title("Repository")
        self.add_backup_win_aws_box.add(self.add_backup_win_aws_repository_row)

        # repository
        self.add_backup_win_repository_box = Adw.PreferencesGroup()
        self.add_backup_win_repository_box.set_margin_top(10)
        self.add_backup_win_repository_box.set_title("Repository")
        self.add_backup_win_repository_box.set_description("The repository to backup to")
        self.add_backup_win_content.append(self.add_backup_win_repository_box)

        self.add_backup_win_repository_password = Adw.PasswordEntryRow()
        self.add_backup_win_repository_password.set_title("Repository Password")
        self.add_backup_win_repository_box.add(self.add_backup_win_repository_password)
        
        self.add_backup_win_source_box = Adw.PreferencesGroup()
        self.add_backup_win_source_box.set_margin_top(10)
        self.add_backup_win_source_box.set_title("Source")
        self.add_backup_win_source_box.set_description("The source to backup")
        self.add_backup_win_content.append(self.add_backup_win_source_box)

        self.add_backup_win_home_row = Adw.SwitchRow()
        self.add_backup_win_home_row.set_title("Home")
        self.add_backup_win_home_row.set_subtitle("Backup the home directory")
        self.add_backup_win_home_row.set_active(True)
        self.add_backup_win_home_row.set_sensitive(False)
        self.add_backup_win_home_row.set_icon_name("user-home-symbolic")
        self.add_backup_win_source_box.add(self.add_backup_win_home_row)
        
        data = b_store.get_backup_config(backup_id)
        if data is not None:
            self.add_backup_win_name_row.set_text(data.settings.name)
            self.add_backup_win_aws_secret_key_row.set_text(data.settings.aws_s3_secret_key)
            self.add_backup_win_aws_access_key_row.set_text(data.settings.aws_s3_access_key)
            self.add_backup_win_aws_repository_row.set_text(data.settings.aws_s3_repository)
            self.add_backup_win_repository_password.set_text(data.settings.repository_password)
            if "sources" in data.settings.__dict__:
                self.add_backup_win_home_row.set_active("~/" in data.settings.sources)

        self.add_backup_win_exclude_box = Adw.PreferencesGroup()
        self.add_backup_win_exclude_box.set_margin_top(10)
        self.add_backup_win_exclude_box.set_title("Exclude")
        self.add_backup_win_exclude_box.set_description("Exclude files from backup")
        self.add_backup_win_content.append(self.add_backup_win_exclude_box)

        self.add_backup_win_exclude_caches_row = Adw.SwitchRow()
        self.add_backup_win_exclude_caches_row.set_title("Exclude Caches")
        self.add_backup_win_exclude_caches_row.set_subtitle("Cache files in ~/.cache, node_modules, etc.")
        self.add_backup_win_exclude_caches_row.set_active(True)
        # disable toggle
        self.add_backup_win_exclude_caches_row.set_sensitive(False)
        self.add_backup_win_exclude_caches_row.set_icon_name("folder-symbolic")
        self.add_backup_win_exclude_box.add(self.add_backup_win_exclude_caches_row)

        self.add_backup_win_exclude_logs_row = Adw.SwitchRow()
        self.add_backup_win_exclude_logs_row.set_title("Trash")
        self.add_backup_win_exclude_logs_row.set_subtitle("Trash files in ~/.local/share/Trash")
        self.add_backup_win_exclude_logs_row.set_active(True)
        # disable toggle
        self.add_backup_win_exclude_logs_row.set_sensitive(False)
        self.add_backup_win_exclude_logs_row.set_icon_name("user-trash-symbolic")
        self.add_backup_win_exclude_box.add(self.add_backup_win_exclude_logs_row)

        self.add_backup_win_exclude_downloads_row = Adw.SwitchRow()
        self.add_backup_win_exclude_downloads_row.set_title("Downloads")
        self.add_backup_win_exclude_downloads_row.set_active(True)
        # disable toggle
        self.add_backup_win_exclude_downloads_row.set_sensitive(False)
        self.add_backup_win_exclude_downloads_row.set_icon_name("folder-download-symbolic")
        self.add_backup_win_exclude_box.add(self.add_backup_win_exclude_downloads_row)

        self.add_backup_win_exclude_videos_row = Adw.SwitchRow()
        self.add_backup_win_exclude_videos_row.set_title("Video Files")
        self.add_backup_win_exclude_videos_row.set_subtitle("mp4, mkv, avi, etc.")
        self.add_backup_win_exclude_videos_row.set_active(True)
        # disabletoggle
        self.add_backup_win_exclude_videos_row.set_sensitive(False)
        self.add_backup_win_exclude_videos_row.set_icon_name("folder-videos-symbolic")
        self.add_backup_win_exclude_box.add(self.add_backup_win_exclude_videos_row)

        self.add_backup_win_exclude_vm_images_row = Adw.SwitchRow()
        self.add_backup_win_exclude_vm_images_row.set_title("VM Images")
        self.add_backup_win_exclude_vm_images_row.set_subtitle("qcow2, vdi, etc.")
        self.add_backup_win_exclude_vm_images_row.set_active(True)
        # disabletoggle
        self.add_backup_win_exclude_vm_images_row.set_sensitive(False)
        self.add_backup_win_exclude_vm_images_row.set_icon_name("computer-symbolic")
        self.add_backup_win_exclude_box.add(self.add_backup_win_exclude_vm_images_row)

        # add button
        self.add_backup_win_add_button = Gtk.Button(label="Save")
        self.add_backup_win_add_button.set_margin_top(20)
        self.add_backup_win_add_button.set_margin_bottom(20)
        self.add_backup_win_add_button.get_style_context().add_class("suggested-action")
        self.add_backup_win_add_button.connect("clicked", lambda _: on_add_backup_win_add_button_clicked(self, b_store))
        self.add_backup_win_content.append(self.add_backup_win_add_button)
    
        self.append(self.add_backup_win_scroll)

def on_add_backup_win_add_button_clicked(self, b_store):
    id = self.add_backup_win_id_row.get_subtitle()
    name = self.add_backup_win_name_row.get_text()
    aws_secret_key = self.add_backup_win_aws_secret_key_row.get_text()
    aws_access_key = self.add_backup_win_aws_access_key_row.get_text()
    aws_repo = self.add_backup_win_aws_repository_row.get_text()
    repo_password = self.add_backup_win_repository_password.get_text()
    sources = []
    if self.add_backup_win_home_row.get_active():
        sources.append("~/")

    res = restic.check_repo_status(aws_repo, aws_access_key, aws_secret_key, repo_password)
    if res == "ok":
        self.navigate_callback("main", None)
        # self.add_backup_win.close()
        cfg = backup_store.BackupConfig(backup_store.BackupSettings(id, name, aws_secret_key, aws_access_key, aws_repo, repo_password, sources), backup_store.BackupStatus(), backup_store.BackupSchedule())
        b_store.add_backup_config(cfg)
        config.save_all_configs(b_store)
    elif res == "norepo":
        print("repo check failed")
        dialog = Adw.MessageDialog.new(None, "No Repository Found")
        dialog.set_body("There was no repository found at the specified location. Do you want to create a new one?")
        dialog.set_title("No Repository Found")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("ok", "Create")
        dialog.set_modal(True)
        dialog.set_visible(True)
        def create_repo(dialog, response_id):
            if response_id == "ok":
                print("create repo")
                result = restic.init(aws_repo, aws_access_key, aws_secret_key, repo_password)
                print("create repo result", result)
                dialog.close()
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