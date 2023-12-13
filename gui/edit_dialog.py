from gi.repository import Gtk, Adw
import backend.config as config
import backend.backup_store as backup_store
import uuid

def show_edit_backup_dialog(self, b_store, backup_id):
    # window
    self.add_backup_win = Gtk.Window(title="Edit Backup")
    self.add_backup_win.set_default_size(600, 600)

    self.add_backup_win_scroll = Gtk.ScrolledWindow()
    self.add_backup_win_scroll.set_vexpand(True)
    self.add_backup_win_scroll.set_hexpand(False)
    self.add_backup_win.set_child(self.add_backup_win_scroll)

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

    self.add_backup_win_source_path_row = Adw.EntryRow()
    self.add_backup_win_source_path_row.set_title("Source Path")
    self.add_backup_win_source_box.add(self.add_backup_win_source_path_row)
    
    data = b_store.get_backup_config(backup_id)
    if data is not None:
        self.add_backup_win_name_row.set_text(data.settings.name)
        self.add_backup_win_aws_secret_key_row.set_text(data.settings.aws_s3_secret_key)
        self.add_backup_win_aws_access_key_row.set_text(data.settings.aws_s3_access_key)
        self.add_backup_win_aws_repository_row.set_text(data.settings.aws_s3_repository)
        self.add_backup_win_repository_password.set_text(data.settings.repository_password)
        self.add_backup_win_source_path_row.set_text(data.settings.source_path)

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
    self.add_backup_win_add_button.get_style_context().add_class("suggested-action")
    self.add_backup_win_add_button.connect("clicked", lambda _: on_add_backup_win_add_button_clicked(self, b_store))
    self.add_backup_win_content.append(self.add_backup_win_add_button)

    self.add_backup_win.present()

def on_add_backup_win_add_button_clicked(self, b_store):
    self.add_backup_win.close()
    cfg = backup_store.BackupConfig(backup_store.BackupSettings(self.add_backup_win_id_row.get_subtitle(), self.add_backup_win_name_row.get_text(), self.add_backup_win_aws_secret_key_row.get_text(), self.add_backup_win_aws_access_key_row.get_text(), self.add_backup_win_aws_repository_row.get_text(), self.add_backup_win_repository_password.get_text(), self.add_backup_win_source_path_row.get_text()), backup_store.BackupStatus(), backup_store.BackupSchedule())
    b_store.add_backup_config(cfg)
    config.save_all_configs(b_store)

    self.box.set_margin_start(80)  
    self.box.set_margin_end(80)
    self.box.set_margin_top(10)