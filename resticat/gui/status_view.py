from gi.repository import Gtk, Adw, GObject
import backend.config as config
from datetime import timedelta

def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

class StatusView(Gtk.Box):
    def __init__(self, b_store, b_executor, navigate_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.b_store= b_store
        self.b_executor = b_executor
        self.navigate_callback = navigate_callback
    
        self.backup_config_view = self
        self.set_margin_start(80)
        self.set_margin_end(80)
        self.set_margin_top(10)

        self.status_box = Gtk.Stack()
        self.status_box.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.status_box.set_transition_duration(200)
        self.backup_config_view.append(self.status_box)

        self.status_idle_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.status_idle_list = Gtk.ListBox()
        self.status_idle_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.status_idle_list.get_style_context().add_class("boxed-list")
        self.status_box_idle = Adw.ActionRow()
        self.status_box_idle.set_title("Idle")
        self.status_box_idle.set_subtitle("Upcoming Backup - Never")
        self.status_idle_list.append(self.status_box_idle)
        self.status_idle_box.append(self.status_idle_list)
        self.status_box.add_named(self.status_idle_box, "idle")
        
        self.status_running_list = Gtk.ListBox()
        self.status_running_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.status_running_list.get_style_context().add_class("boxed-list")
        
        self.status_box_running = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.status_box_running.set_margin_start(10)
        self.status_box_running.set_margin_end(10)
        self.status_box_running.set_margin_top(10)
        self.status_box_running.set_margin_bottom(10)
        self.running_title = Gtk.Label(label="Backing up...")
        self.running_title.set_markup("<b>Backing up...</b>")
        self.running_title.set_halign(Gtk.Align.START)
        self.status_box_running.append(self.running_title)

        self.subtitle = Gtk.Label(label="Calculating time remaining")
        self.subtitle.set_halign(Gtk.Align.START)
        self.subtitle.get_style_context().add_class("dim-label")
        self.status_box_running.append(self.subtitle)

        self.files_progress = Gtk.Label(label="0/0 files")
        self.files_progress.set_halign(Gtk.Align.START)
        self.files_progress.get_style_context().add_class("dim-label")
        self.status_box_running.append(self.files_progress)

        self.data_progress = Gtk.Label(label="0/0 bytes")
        self.data_progress.set_halign(Gtk.Align.START)
        self.data_progress.get_style_context().add_class("dim-label")
        self.status_box_running.append(self.data_progress)
    
        self.current_file_label = Gtk.Label(label="Current file")
        self.current_file_label.set_halign(Gtk.Align.START)
        self.current_file_label.get_style_context().add_class("dim-label")
        self.status_box_running.append(self.current_file_label)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(False)
        self.progress_bar.set_fraction(0)
        self.progress_bar.set_hexpand(True)
        self.progress_bar.set_margin_end(10)
        self.status_box_running.append(self.progress_bar)
        self.status_running_list.append(self.status_box_running)
        self.status_box.add_named(self.status_running_list, "running")


        self.error_box = Adw.ActionRow()
        self.error_box.set_title("Error")
        self.error_box.set_subtitle("Failed to backup")
        self.error_box.set_activatable(True)
        self.error_box.set_icon_name("dialog-error-symbolic")
        self.status_box.add_named(self.error_box, "error")

        # take up empty space
        self.empty_space_row = Gtk.Box()
        self.empty_space_row.set_vexpand(True)
        self.backup_config_view.append(self.empty_space_row)

        self.action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.action_box.set_halign(Gtk.Align.CENTER)
        self.action_box.set_margin_bottom(10)

        self.backup_config_view_back_button = Gtk.Button(label="Backup Now")
        self.backup_config_view_back_button.get_style_context().add_class("suggested-action")
        self.backup_config_view_back_button.connect("clicked", lambda _: b_executor.backup_now(self.selected_id))
        self.backup_config_view_back_button.get_style_context().add_class("pill")
        self.action_box.append(self.backup_config_view_back_button)

        self.backup_config_view_clean_button = Gtk.Button(label="Clean Now")
        self.backup_config_view_clean_button.get_style_context().add_class("suggested-action")
        self.backup_config_view_clean_button.get_style_context().add_class("pill")
        self.backup_config_view_clean_button.connect("clicked", lambda _: b_executor.clean_now(self.selected_id))
        self.action_box.append(self.backup_config_view_clean_button)
        
        self.backup_config_view_delete_button = Gtk.Button(label="Delete Backup")
        self.backup_config_view_delete_button.get_style_context().add_class("destructive-action")
        self.backup_config_view_delete_button.get_style_context().add_class("pill")
        self.backup_config_view_delete_button.connect("clicked", lambda _: b_store.remove_backup_config(self.selected_id) and config.save_all_configs() and self.switch_to_overview())
        self.action_box.append(self.backup_config_view_delete_button)
        self.backup_config_view.append(self.action_box)

        self.destroyed = False
        self.last_status = None

        def update_timer():
            if not self.destroyed:
                GObject.timeout_add(1000, update_timer)
            
            if not "selected_id" in self.__dict__:
                return

            backup_config = b_store.get_backup_config(self.selected_id)
            if backup_config is None:
                return
            
            if backup_config.status.status == "Idle" and self.last_status != "Idle":
                self.status_box.set_visible_child_name("idle")
            elif backup_config.status.status == "Running" and self.last_status != "Running":
                self.status_box.set_visible_child_name("running")
                self.running_title.set_text(backup_config.status.message)
            elif backup_config.status.status == "Error" and self.last_status != "Error":
                self.status_box.set_visible_child_name("error")
            self.last_status = backup_config.status.status


            self.progress_bar.set_fraction(backup_config.status.progress)
            self.progress_bar.set_text(str(round(backup_config.status.progress * 100, 2))+ "%")
            if "files" in backup_config.status.__dict__:
                self.files_progress.set_text("{}/{} files".format(int(round(backup_config.status.files, 1)), backup_config.status.max_files))
            else:
                print("no files in status")
                self.files_progress.set_text("0/0 files")
            self.data_progress.set_text("{}/{}".format(sizeof_fmt(backup_config.status.bytes_processed), sizeof_fmt(backup_config.status.bytes_total)))
            current_file = backup_config.status.message
            if len(current_file) > 70:
                current_file = current_file[:70] + "..."
            self.current_file_label.set_text(current_file)
            # self.current_file_label.set_text(current_file)
            if "seconds_remaining" in backup_config.status.__dict__:
                if backup_config.status.seconds_remaining is not None:
                    if backup_config.status.seconds_remaining > 60 * 60:
                        self.subtitle.set_text("{} hours, {} minutes remainaing".format(int(backup_config.status.seconds_remaining / 60 / 60), int(backup_config.status.seconds_remaining / 60 % 60)))
                    elif backup_config.status.seconds_remaining > 60:
                        self.subtitle.set_text("{} minutes remaining".format(int(backup_config.status.seconds_remaining / 60)))
                    else:
                        self.subtitle.set_text("{} seconds remaining".format(int(backup_config.status.seconds_remaining)))
                else:
                    self.subtitle.set_text("Calculating time remaining")
            self.backup_config_view_back_button.set_sensitive(backup_config.status.status == "Idle")
            if backup_config.status.status == "Running" or backup_config.status.status == "Running-Cleanup":
                # set enabled
                self.backup_config_view_back_button.set_sensitive(False)
                self.backup_config_view_clean_button.set_sensitive(False)
            else:
                self.backup_config_view_back_button.set_sensitive(True)
                self.backup_config_view_clean_button.set_sensitive(True)
            
            if not backup_config.schedule.backup_schedule_enabled:
                self.status_box_idle.set_subtitle("Scheduled Backup disabled")
            else:
                if backup_config.status.last_backup is None:
                    self.status_box_idle.set_subtitle("No Upcoming Backup")    
                else:
                    next_backup_time = backup_config.status.last_backup + timedelta(hours=(1 if backup_config.schedule.backup_frequency == "hourly" else (24 if backup_config.schedule.backup_frequency == "daily" else 7 * 24)))
                    self.status_box_idle.set_subtitle("Upcoming Backup - {}".format(next_backup_time.strftime("%H:%M")))
        GObject.timeout_add(1000, lambda: update_timer())

    def navigate_to(self, param, window):
        self.selected_id = param
        self.header = Gtk.HeaderBar()
        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect("clicked", lambda _: self.navigate_callback("main", None))
        self.header.pack_start(self.back_button)
        window.set_titlebar(self.header)