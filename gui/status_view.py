from gi.repository import Gtk, Adw, GObject
import backend.config as config
from datetime import timedelta

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

        # title
        self.backup_config_view_title = Gtk.Label(label="")
        self.backup_config_view_title.set_markup("<b>Backup</b>")
        self.backup_config_view_title.set_halign(Gtk.Align.START)
        self.backup_config_view.append(self.backup_config_view_title)

        self.backup_config_view_status_box = Gtk.ListBox()
        self.backup_config_view_status_box.get_style_context().add_class("boxed-list")
        self.backup_config_view_status_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.backup_config_view_status_box.connect("row-activated", lambda listbox, button: self.show_edit_backup_dialog(listbox, self.selected_id))
        self.backup_config_view.append(self.backup_config_view_status_box)
        
        self.status_row = Gtk.ListBoxRow()
        self.status_row.set_selectable(False)
        self.backup_config_view_status_box.append(self.status_row)

        self.status_box = Gtk.Stack()
        self.status_box.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.status_box.set_transition_duration(200)
        self.status_row.set_child(self.status_box)

        self.status_box_idle = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.status_box_idle.set_margin_start(10)
        self.status_box_idle.set_margin_end(10)
        self.status_box_idle.set_margin_top(10)
        self.status_box_idle.set_margin_bottom(10)
        self.title = Gtk.Label(label="Idle")
        self.title.set_markup("<b>Idle</b>")
        self.title.set_halign(Gtk.Align.START)
        self.status_box_idle.append(self.title)
        self.status_box_idle_description_label = Gtk.Label(label="Upcoming Backup - 12:00")
        self.status_box_idle_description_label.set_halign(Gtk.Align.START)
        self.status_box_idle_description_label.get_style_context().add_class("dim-label")
        self.status_box_idle.append(self.status_box_idle_description_label)
        self.status_box.add_named(self.status_box_idle, "idle ")

        self.status_box_running = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.status_box_running.set_margin_start(10)
        self.status_box_running.set_margin_end(10)
        self.status_box_running.set_margin_top(10)
        self.status_box_running.set_margin_bottom(10)
        self.title = Gtk.Label(label="Backing up...")
        self.title.set_markup("<b>Backing up...</b>")
        self.title.set_halign(Gtk.Align.START)
        self.status_box_running.append(self.title)

        self.subtitle = Gtk.Label(label="Calculating time remaining")
        self.subtitle.set_halign(Gtk.Align.START)
        self.subtitle.get_style_context().add_class("dim-label")
        self.status_box_running.append(self.subtitle)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(False)
        self.progress_bar.set_fraction(0)
        self.progress_bar.set_hexpand(True)
        self.progress_bar.set_margin_end(10)
        self.status_box_running.append(self.progress_bar)
        self.status_box.add_named(self.status_box_running, "running")

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
        # set align to middle
        self.action_box.set_halign(Gtk.Align.CENTER)

        self.backup_config_view_back_button = Gtk.Button(label="Backup Now")
        self.backup_config_view_back_button.get_style_context().add_class("suggested-action")
        self.backup_config_view_back_button.connect("clicked", lambda _: b_executor.backup_now(self.selected_id))
        # do not stretch
        self.backup_config_view_back_button.get_style_context().add_class("pill")
        self.action_box.append(self.backup_config_view_back_button)

        self.backup_config_view_clean_button = Gtk.Button(label="Clean Now")
        self.backup_config_view_clean_button.get_style_context().add_class("suggested-action")
        self.backup_config_view_clean_button.get_style_context().add_class("pill")
        self.backup_config_view_clean_button.connect("clicked", lambda _: b_executor.clean_now(self.selected_id))
        # do not stretch
        self.action_box.append(self.backup_config_view_clean_button)
        
        self.backup_config_view_delete_button = Gtk.Button(label="Delete Backup")
        self.backup_config_view_delete_button.get_style_context().add_class("destructive-action")
        self.backup_config_view_delete_button.get_style_context().add_class("pill")
        self.backup_config_view_delete_button.connect("clicked", lambda _: b_store.remove_backup_config(self.selected_id) and config.save_all_configs() and self.switch_to_overview())
        # do not stretch
        self.action_box.append(self.backup_config_view_delete_button)
        self.backup_config_view.append(self.action_box)

        self.backup_config_view_status_box.destroyed = False
        self.last_status = None

        def update_timer():
            if not "selected_id" in self.__dict__:
                return

            backup_config = b_store.get_backup_config(self.selected_id)
            if backup_config is None:
                return
            
            if backup_config.status.status == "Idle" and self.last_status != "Idle":
                self.status_box.set_visible_child_name("idle")
            elif backup_config.status.status == "Running" and self.last_status != "Running":
                self.status_box.set_visible_child_name("running")
            elif backup_config.status.status == "Error" and self.last_status != "Error":
                self.status_box.set_visible_child_name("error")
            self.last_status = backup_config.status.status

            

            # self.backup_config_view_status_row.set_title("<b>"+backup_config.settings.name+"</b>")
            # self.backup_config_view_status_row.set_subtitle("S3 Provider")
            # self.progress_box_title.set_text("Backing up...")
            # if not backup_config.status.files is None:
            #     self.progress_box_description_label.set_text("{}/{} files".format(int(round(backup_config.status.files, 1)), backup_config.status.max_files))
            self.progress_bar.set_fraction(backup_config.status.progress)
            self.progress_bar.set_text(str(round(backup_config.status.progress * 100, 2))+ "%")
            current_file = backup_config.status.message
            if len(current_file) > 70:
                current_file = current_file[:70] + "..."
            # self.current_file_label.set_text(current_file)
            # self.eta_label.set_text("Elapsed: {}s, Remaining: {}s".format(backup_config.status.seconds_elapsed, backup_config.status.seconds_remaining))
            self.backup_config_view_back_button.set_sensitive(backup_config.status.status == "Idle")
            if backup_config.status.status == "Running" or backup_config.status.status == "Running-Cleanup":
                # set enabled
                self.backup_config_view_back_button.set_sensitive(False)
                self.backup_config_view_clean_button.set_sensitive(False)
            else:
                self.backup_config_view_back_button.set_sensitive(True)
                self.backup_config_view_clean_button.set_sensitive(True)
            
            if not backup_config.schedule.backup_schedule_enabled:
                self.status_box_idle_description_label.set_text("Scheduled Backup disabled")
            else:
                if backup_config.status.last_backup is None:
                    self.status_box_idle_description_label.set_text("Upcoming Backup - Never")
                else:
                    next_backup_time = backup_config.status.last_backup + timedelta(hours=(1 if backup_config.schedule.backup_frequency == "hourly" else (24 if backup_config.schedule.backup_frequency == "daily" else 7 * 24)))
                    self.status_box_idle_description_label.set_text("Upcoming Backup - {}".format(next_backup_time.strftime("%H:%M")))

            if not self.backup_config_view_status_box.destroyed:
                GObject.timeout_add(100, update_timer)
        GObject.timeout_add(100, lambda: update_timer())

    def navigate_to(self, param, window):
        self.header = Gtk.HeaderBar()
        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect("clicked", lambda _: self.navigate_callback("main", None))
        self.header.pack_start(self.back_button)
        window.set_titlebar(self.header)