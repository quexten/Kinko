import sys
import gi
import uuid
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, Graphene, Gsk, Gio, GLib, GObject
import backend.backup_store as backup_store
import backend.backup_executor as backup_executor
import event_monitors.power_monitor as power_monitor
import event_monitors.network_monitor as network_monitor
from datetime import timedelta
from gui.backup_config_list_entry import create_backup_preview_box

import backend.config as config

b = backup_store.BackupStore()
configs = config.read_all_configs()
for cfg in configs:
    b.add_backup_config(cfg)

be = backup_executor.BackupExecutor(b)
power_monitor.start_monitor(be)
network_monitor.start_monitor(be)

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.backup_overview = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.backup_schedule_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_schedule_view.set_margin_start(80)
        self.backup_schedule_view.set_margin_end(80)
        self.backup_schedule_view.set_margin_top(10)
        self.backup_schedule_view.set_margin_bottom(10)

        self.backup_config_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_config_view.set_margin_start(80)
        self.backup_config_view.set_margin_end(80)
        self.backup_config_view.set_margin_top(10)
        self.backup_config_view.set_margin_bottom(30)

        self.backup_overview_scroll = Gtk.ScrolledWindow()
        self.backup_overview_scroll.set_child(self.backup_overview)
        self.backup_overview_scroll.set_vexpand(True)
        self.backup_config_view_scroll = Gtk.ScrolledWindow()
        self.backup_config_view_scroll.set_child(self.backup_config_view)
        self.backup_config_view_scroll.set_vexpand(True)

        self.backup_history = Gtk.ScrolledWindow()
        self.backup_history.set_child(self.backup_schedule_view)
        self.backup_history.set_vexpand(True)

        # schedule
        self.schedule_config = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.schedule_config.set_margin_start(80)
        self.schedule_config.set_margin_end(80)
        self.schedule_config.set_margin_top(10)
        self.schedule_config.set_margin_bottom(10)
        self.schedule_config_scroll = Gtk.ScrolledWindow()
        self.schedule_config_scroll.set_child(self.schedule_config)
        self.schedule_config_scroll.set_vexpand(True)

        self.stack.add_named(self.backup_overview_scroll, "overview" )
        self.stack.add_named(self.backup_config_view_scroll, "details" )
        self.stack.add_named(self.schedule_config_scroll, "schedule" )
        self.stack.add_named(self.backup_history, "backup_schedule")
        self.set_child(self.stack)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_overview.append(self.box)

        for backup_config in b.get_backup_configs():
            self.box.append(create_backup_preview_box(backup_config, self.view_details, self.view_schedule, self.view_backup_history, self.show_edit_backup_dialog))

        self.box.set_margin_start(80)  
        self.box.set_margin_end(80)
        self.box.set_margin_top(10)
        self.set_default_size(800, 500)
        self.set_title("Resticat")

        self.box.append(self.stack)

        self.switch_to_overview()

    def switch_to_details(self, id):
        self.header = Gtk.HeaderBar()
        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect("clicked", lambda _: self.switch_to_overview())
        self.header.pack_start(self.back_button)
        self.set_titlebar(self.header)

        self.stack.set_visible_child(self.backup_config_view_scroll)

    def switch_to_overview(self):
        if not "header" in locals():
            def update():
                while self.box.get_first_child() is not None:
                    self.box.get_first_child().on_destroy()
                    self.box.remove(self.box.get_first_child())

                for backup_config in b.get_backup_configs():
                    self.box.append(create_backup_preview_box(backup_config, self.view_details, self.view_schedule, self.view_backup_history, self.show_edit_backup_dialog))
            b.on_update(lambda: GLib.idle_add(update))
            b.notify_update()
        
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)
        self.back_button = Gtk.Button(label="Add Backup")
        self.back_button.get_style_context().add_class("suggested-action")
        self.back_button.connect("clicked", lambda _: self.show_edit_backup_dialog())
        self.header.pack_start(self.back_button)

        self.stack.set_visible_child(self.backup_overview_scroll)

    def switch_to_schedule(self):
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)
        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect("clicked", lambda _: self.switch_to_overview())
        self.header.pack_start(self.back_button)
        self.stack.set_visible_child(self.schedule_config_scroll)

    def switch_to_backup_history(self):
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)
        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect("clicked", lambda _: self.switch_to_overview())
        self.header.pack_start(self.back_button)
        self.stack.set_visible_child(self.backup_history)

        if hasattr(self, "history_initialized") is False:
            self.history_initialized = True
            #history label
            self.history_label = Gtk.Label(label="")
            self.history_label.set_markup("<b>History</b>")
            self.history_label.set_halign(Gtk.Align.START)
            self.backup_schedule_view.append(self.history_label)

            # history list
            self.history_list = Gtk.ListBox()
            self.history_list.get_style_context().add_class("boxed-list")
            self.history_list.set_selection_mode(Gtk.SelectionMode.NONE)
            self.history_list.connect("row-activated", lambda listbox, button: self.show_edit_backup_dialog(listbox, self.selected_id))
            self.backup_schedule_view.append(self.history_list)

        while self.history_list.get_first_child() is not None:
            self.history_list.remove(self.history_list.get_first_child())

        for backup in reversed(b.get_backup_config(self.selected_id).status.backups):
            row = Adw.ActionRow()

            row.set_title(backup.get("time").strftime("%Y-%m-%d %H:%M:%S"))
            row.set_subtitle(backup.get("short_id"))
            row.set_icon_name("emblem-default-symbolic")

            self.history_list.append(row)

    def view_schedule(self, listbox, button, id):
        self.selected_id = id
        self.switch_to_schedule()
        if hasattr(self, "backup_schedule_view_backup_settings") is False:
            self.backup_schedule_view_backup_settings = Adw.PreferencesGroup()
            self.backup_schedule_view_backup_settings.set_title("Backup Settings")
            self.backup_schedule_view_backup_settings.set_description("Backup Settings")
            self.schedule_config.append(self.backup_schedule_view_backup_settings)

            # allow on mobile
            self.backup_schedule_view_backup_settings_allow_on_metered_row = Adw.SwitchRow()
            self.backup_schedule_view_backup_settings_allow_on_metered_row.set_title("Allow on metered networks")
            self.backup_schedule_view_backup_settings_allow_on_metered_row.set_active(True)
            self.backup_schedule_view_backup_settings_allow_on_metered_row.set_icon_name("network-cellular-symbolic")
            def on_allow_on_metered_changed(switch, gparam):
                b.get_backup_config(self.selected_id).schedule.allow_on_metered = switch.get_active()
            self.backup_schedule_view_backup_settings_allow_on_metered_row.connect("notify::active", on_allow_on_metered_changed)
            self.backup_schedule_view_backup_settings.add(self.backup_schedule_view_backup_settings_allow_on_metered_row)

            self.backup_schedule_view_backup_schedule_group = Adw.PreferencesGroup()
            self.backup_schedule_view_backup_schedule_group.set_title("Preferences")
            self.backup_schedule_view_backup_schedule_group.set_description("Backup Schedule")
            self.backup_schedule_view_backup_schedule_group.set_margin_top(20)
            self.schedule_config.append(self.backup_schedule_view_backup_schedule_group)

            self.backup_schedule_view_preferences_on_connect_to_wifi_row = Adw.SwitchRow()
            self.backup_schedule_view_preferences_on_connect_to_wifi_row.set_title("Backup on Network Connection")
            self.backup_schedule_view_preferences_on_connect_to_wifi_row.set_active(True)
            self.backup_schedule_view_preferences_on_connect_to_wifi_row.set_icon_name("network-wireless-symbolic")
            def on_on_connect_to_wifi_changed(switch, gparam):
                b.get_backup_config(self.selected_id).schedule.on_network = switch.get_active()
            self.backup_schedule_view_preferences_on_connect_to_wifi_row.connect("notify::active", on_on_connect_to_wifi_changed)
            self.backup_schedule_view_backup_schedule_group.add(self.backup_schedule_view_preferences_on_connect_to_wifi_row)

            self.backup_schedule_view_preferences_on_connect_to_power_row = Adw.SwitchRow()
            self.backup_schedule_view_preferences_on_connect_to_power_row.set_title("Backup on connect to power")
            self.backup_schedule_view_preferences_on_connect_to_power_row.set_active(True)
            self.backup_schedule_view_preferences_on_connect_to_power_row.set_icon_name("battery-full-charging-symbolic")
            def on_on_connect_to_power_changed(switch, gparam):
                b.get_backup_config(self.selected_id).schedule.on_ac = switch.get_active()
            self.backup_schedule_view_preferences_on_connect_to_power_row.connect("notify::active", on_on_connect_to_power_changed)
            self.backup_schedule_view_backup_schedule_group.add(self.backup_schedule_view_preferences_on_connect_to_power_row)

            self.backup_schedule_view_preferences_backup_enaled_row = Adw.SwitchRow()
            self.backup_schedule_view_preferences_backup_enaled_row.set_title("Perform Backups Reguraly")
            self.backup_schedule_view_preferences_backup_enaled_row.set_active(True)
            self.backup_schedule_view_backup_schedule_group.add(self.backup_schedule_view_preferences_backup_enaled_row)

            self.backup_schedule_view_preferences_backup_frequency_row = Adw.ComboRow()
            self.backup_schedule_view_preferences_backup_frequency_row.set_title("Frequency")
            self.backup_schedule_view_preferences_backup_frequency_row.set_subtitle("Every 24 hours")
            self.backup_schedule_view_preferences_backup_frequency_row.set_icon_name("x-office-calendar-symbolic")
            model = Gio.ListStore()
            options = Gtk.StringList.new(["Hourly", "Daily", "Weekly"])

            self.backup_schedule_view_preferences_backup_frequency_row.set_model(options)
            self.backup_schedule_view_backup_schedule_group.add(self.backup_schedule_view_preferences_backup_frequency_row)
            def on_backup_enabled_changed(switch, gparam):
                b.get_backup_config(self.selected_id).schedule.backup_schedule_enabled = switch.get_active()
                self.backup_schedule_view_preferences_backup_frequency_row.set_sensitive(switch.get_active())
            self.backup_schedule_view_preferences_backup_enaled_row.connect("notify::active", on_backup_enabled_changed)


            # clean up
            self.backup_schedule_view_cleanup = Adw.PreferencesGroup()
            self.backup_schedule_view_cleanup.set_title("Cleanup")
            self.backup_schedule_view_cleanup.set_description("Cleanup settings")
            self.backup_schedule_view_cleanup.set_margin_top(20)
            self.schedule_config.append(self.backup_schedule_view_cleanup)

            self.backup_schedule_view_cleanup_enabled_row = Adw.SwitchRow()
            self.backup_schedule_view_cleanup_enabled_row.set_title("Cleanup")
            self.backup_schedule_view_cleanup_enabled_row.set_active(True)
            self.backup_schedule_view_cleanup_enabled_row.set_icon_name("x-office-calendar-symbolic")
            self.backup_schedule_view_cleanup.add(self.backup_schedule_view_cleanup_enabled_row)

            self.backup_schedule_view_cleanup_keep_hourly_row = Adw.SpinRow()
            self.backup_schedule_view_cleanup_keep_hourly_row.set_title("Keep Hourly")
            self.backup_schedule_view_cleanup_keep_hourly_row.set_value(24)
            self.backup_schedule_view_cleanup_keep_hourly_row.set_range(0, 1000)
            self.backup_schedule_view_cleanup_keep_hourly_row.get_adjustment().set_step_increment(1)
            self.backup_schedule_view_cleanup.add(self.backup_schedule_view_cleanup_keep_hourly_row)

            self.backup_schedule_view_cleanup_keep_daily_row = Adw.SpinRow()
            self.backup_schedule_view_cleanup_keep_daily_row.set_title("Keep Daily")
            self.backup_schedule_view_cleanup_keep_daily_row.set_value(7)
            self.backup_schedule_view_cleanup_keep_daily_row.set_range(0, 1000)
            self.backup_schedule_view_cleanup_keep_daily_row.get_adjustment().set_step_increment(1)
            self.backup_schedule_view_cleanup.add(self.backup_schedule_view_cleanup_keep_daily_row)

            self.backup_schedule_view_cleanup_keep_weekly_row = Adw.SpinRow()
            self.backup_schedule_view_cleanup_keep_weekly_row.set_title("Keep Weekly")
            self.backup_schedule_view_cleanup_keep_weekly_row.set_value(4)
            self.backup_schedule_view_cleanup_keep_weekly_row.set_range(0, 1000)
            self.backup_schedule_view_cleanup_keep_weekly_row.get_adjustment().set_step_increment(1)
            self.backup_schedule_view_cleanup.add(self.backup_schedule_view_cleanup_keep_weekly_row)

            self.backup_schedule_view_cleanup_keep_monthly_row = Adw.SpinRow()
            self.backup_schedule_view_cleanup_keep_monthly_row.set_title("Keep Monthly")
            self.backup_schedule_view_cleanup_keep_monthly_row.set_value(6)
            self.backup_schedule_view_cleanup_keep_monthly_row.set_range(0, 1000)
            self.backup_schedule_view_cleanup_keep_monthly_row.get_adjustment().set_step_increment(1)
            self.backup_schedule_view_cleanup.add(self.backup_schedule_view_cleanup_keep_monthly_row)
            
            self.backup_schedule_view_cleanup_keep_yearly_row = Adw.SpinRow()
            self.backup_schedule_view_cleanup_keep_yearly_row.set_title("Keep Yearly")
            self.backup_schedule_view_cleanup_keep_yearly_row.set_value(1)
            self.backup_schedule_view_cleanup_keep_yearly_row.set_range(0, 1000)
            self.backup_schedule_view_cleanup_keep_yearly_row.get_adjustment().set_step_increment(1)
            self.backup_schedule_view_cleanup.add(self.backup_schedule_view_cleanup_keep_yearly_row)

            def on_cleanup_enabled_changed(switch, gparam):
                b.get_backup_config(self.selected_id).schedule.cleanup_schedule_enabled = switch.get_active()
                self.backup_schedule_view_cleanup_keep_hourly_row.set_sensitive(switch.get_active())
                self.backup_schedule_view_cleanup_keep_monthly_row.set_sensitive(switch.get_active())
            on_cleanup_enabled_changed(self.backup_schedule_view_cleanup_enabled_row, None)
            self.backup_schedule_view_cleanup_enabled_row.connect("notify::active", on_cleanup_enabled_changed)

        # set values
        backup_schedule = b.get_backup_config(id).schedule
        if backup_schedule is None:
            return
        self.backup_schedule_view_backup_settings_allow_on_metered_row.set_active(backup_schedule.allow_on_metered)
        self.backup_schedule_view_preferences_on_connect_to_wifi_row.set_active(backup_schedule.on_network)
        self.backup_schedule_view_preferences_on_connect_to_power_row.set_active(backup_schedule.on_ac)

    def view_details(self, listbox, button, id):
        self.selected_id = id
        
        self.switch_to_details("a")
        if hasattr(self, "backup_config_view_status_box") is False:
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
            self.backup_config_view_back_button.connect("clicked", lambda _: be.backup_now(self.selected_id))
            # do not stretch
            self.backup_config_view_back_button.get_style_context().add_class("pill")
            self.action_box.append(self.backup_config_view_back_button)

            self.backup_config_view_clean_button = Gtk.Button(label="Clean Now")
            self.backup_config_view_clean_button.get_style_context().add_class("suggested-action")
            self.backup_config_view_clean_button.get_style_context().add_class("pill")
            self.backup_config_view_clean_button.connect("clicked", lambda _: be.clean_now(self.selected_id))
            # do not stretch
            self.action_box.append(self.backup_config_view_clean_button)
            
            self.backup_config_view_delete_button = Gtk.Button(label="Delete Backup")
            self.backup_config_view_delete_button.get_style_context().add_class("destructive-action")
            self.backup_config_view_delete_button.get_style_context().add_class("pill")
            self.backup_config_view_delete_button.connect("clicked", lambda _: b.remove_backup_config(self.selected_id) and config.save_all_configs() and self.switch_to_overview())
            # do not stretch
            self.action_box.append(self.backup_config_view_delete_button)
            self.backup_config_view.append(self.action_box)

            self.backup_config_view_status_box.destroyed = False
            self.last_status = None

            def update_timer():
                backup_config = b.get_backup_config(self.selected_id)
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
        
    def view_backup_history(self, listbox, button, id):
        self.selected_id = id
        self.switch_to_backup_history()

    def show_edit_backup_dialog(self, backup_id=None):
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
        
        data = b.get_backup_config(backup_id)
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
        self.add_backup_win_add_button.connect("clicked", self.on_add_backup_win_add_button_clicked)
        self.add_backup_win_content.append(self.add_backup_win_add_button)

        self.add_backup_win.present()

    def on_add_backup_win_add_button_clicked(self, btn):
        self.add_backup_win.close()
        cfg = backup_store.BackupConfig(backup_store.BackupSettings(self.add_backup_win_id_row.get_subtitle(), self.add_backup_win_name_row.get_text(), self.add_backup_win_aws_secret_key_row.get_text(), self.add_backup_win_aws_access_key_row.get_text(), self.add_backup_win_aws_repository_row.get_text(), self.add_backup_win_repository_password.get_text(), self.add_backup_win_source_path_row.get_text()), backup_store.BackupStatus(), backup_store.BackupSchedule())
        b.add_backup_config(cfg)
        b.notify_update()
        config.save_all_configs(b)

        self.box.set_margin_start(80)  
        self.box.set_margin_end(80)
        self.box.set_margin_top(10)

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