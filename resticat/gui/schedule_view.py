from gi.repository import Gtk, Adw, Gio
import backend.config as config

class ScheduleView(Gtk.Box):

    def __init__(self, backup_store, navigate_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_store = backup_store
        self.navigate_callback = navigate_callback
        self.set_margin_start(80)
        self.set_margin_end(80)
        self.set_margin_top(20)

        self.schedule_config = self

        self.backup_schedule_view_backup_settings = Adw.PreferencesGroup()
        self.backup_schedule_view_backup_settings.set_title("Backup Settings")
        self.backup_schedule_view_backup_settings.set_description("Backup Settings")
        self.append(self.backup_schedule_view_backup_settings)

        self.backup_schedule_view_backup_settings_allow_on_metered_row = Adw.SwitchRow()
        self.backup_schedule_view_backup_settings_allow_on_metered_row.set_title("Allow on metered networks")
        self.backup_schedule_view_backup_settings_allow_on_metered_row.set_active(True)
        self.backup_schedule_view_backup_settings_allow_on_metered_row.set_icon_name("network-cellular-symbolic")
        def on_allow_on_metered_changed(switch, gparam):
            backup_store.get_backup_config(self.selected_id).schedule.allow_on_metered = switch.get_active()
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
            backup_store.get_backup_config(self.selected_id).schedule.on_network = switch.get_active()
        self.backup_schedule_view_preferences_on_connect_to_wifi_row.connect("notify::active", on_on_connect_to_wifi_changed)
        self.backup_schedule_view_backup_schedule_group.add(self.backup_schedule_view_preferences_on_connect_to_wifi_row)

        self.backup_schedule_view_preferences_on_connect_to_power_row = Adw.SwitchRow()
        self.backup_schedule_view_preferences_on_connect_to_power_row.set_title("Backup on connect to power")
        self.backup_schedule_view_preferences_on_connect_to_power_row.set_active(True)
        self.backup_schedule_view_preferences_on_connect_to_power_row.set_icon_name("battery-full-charging-symbolic")
        def on_on_connect_to_power_changed(switch, gparam):
            backup_store.get_backup_config(self.selected_id).schedule.on_ac = switch.get_active()
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
            backup_store.get_backup_config(self.selected_id).schedule.backup_schedule_enabled = switch.get_active()
            self.backup_schedule_view_preferences_backup_frequency_row.set_sensitive(switch.get_active())
        self.backup_schedule_view_preferences_backup_enaled_row.connect("notify::active", on_backup_enabled_changed)
        def on_backup_frequency_changed(selection, gparam):
            selected = selection.get_selected()
            if selected == 0:
                backup_store.get_backup_config(self.selected_id).schedule.backup_frequency = "hourly"
            elif selected == 1:
                backup_store.get_backup_config(self.selected_id).schedule.backup_frequency = "daily"
            elif selected == 2:
                backup_store.get_backup_config(self.selected_id).schedule.backup_frequency = "weekly"
            backup_schedule = self.backup_store.get_backup_config(self.selected_id).schedule
            self.backup_schedule_view_preferences_backup_frequency_row.set_subtitle("Every 24 hours" if backup_schedule.backup_frequency == "daily" else "Every 7 days" if backup_schedule.backup_frequency == "weekly" else "Every hour")
        self.backup_schedule_view_preferences_backup_frequency_row.connect("notify::selected", on_backup_frequency_changed)


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
        def on_cleanup_keep_hourly_changed(switch, gparam):
            backup_store.get_backup_config(self.selected_id).schedule.cleanup_keep_hourly = switch.get_value()
        self.backup_schedule_view_cleanup_keep_hourly_row.connect("notify::value", on_cleanup_keep_hourly_changed)

        self.backup_schedule_view_cleanup_keep_daily_row = Adw.SpinRow()
        self.backup_schedule_view_cleanup_keep_daily_row.set_title("Keep Daily")
        self.backup_schedule_view_cleanup_keep_daily_row.set_value(7)
        self.backup_schedule_view_cleanup_keep_daily_row.set_range(0, 1000)
        self.backup_schedule_view_cleanup_keep_daily_row.get_adjustment().set_step_increment(1)
        self.backup_schedule_view_cleanup.add(self.backup_schedule_view_cleanup_keep_daily_row)
        def on_cleanup_keep_daily_changed(switch, gparam):
            backup_store.get_backup_config(self.selected_id).schedule.cleanup_keep_daily = switch.get_value()
        self.backup_schedule_view_cleanup_keep_daily_row.connect("notify::value", on_cleanup_keep_daily_changed)

        self.backup_schedule_view_cleanup_keep_weekly_row = Adw.SpinRow()
        self.backup_schedule_view_cleanup_keep_weekly_row.set_title("Keep Weekly")
        self.backup_schedule_view_cleanup_keep_weekly_row.set_value(4)
        self.backup_schedule_view_cleanup_keep_weekly_row.set_range(0, 1000)
        self.backup_schedule_view_cleanup_keep_weekly_row.get_adjustment().set_step_increment(1)
        self.backup_schedule_view_cleanup.add(self.backup_schedule_view_cleanup_keep_weekly_row)
        def on_cleanup_keep_weekly_changed(switch, gparam):
            backup_store.get_backup_config(self.selected_id).schedule.cleanup_keep_weekly = switch.get_value()
        self.backup_schedule_view_cleanup_keep_weekly_row.connect("notify::value", on_cleanup_keep_weekly_changed)

        self.backup_schedule_view_cleanup_keep_monthly_row = Adw.SpinRow()
        self.backup_schedule_view_cleanup_keep_monthly_row.set_title("Keep Monthly")
        self.backup_schedule_view_cleanup_keep_monthly_row.set_value(6)
        self.backup_schedule_view_cleanup_keep_monthly_row.set_range(0, 1000)
        self.backup_schedule_view_cleanup_keep_monthly_row.get_adjustment().set_step_increment(1)
        self.backup_schedule_view_cleanup.add(self.backup_schedule_view_cleanup_keep_monthly_row)
        def on_cleanup_keep_monthly_changed(switch, gparam):
            backup_store.get_backup_config(self.selected_id).schedule.cleanup_keep_monthly = switch.get_value()
        self.backup_schedule_view_cleanup_keep_monthly_row.connect("notify::value", on_cleanup_keep_monthly_changed)

        self.backup_schedule_view_cleanup_keep_yearly_row = Adw.SpinRow()
        self.backup_schedule_view_cleanup_keep_yearly_row.set_title("Keep Yearly")
        self.backup_schedule_view_cleanup_keep_yearly_row.set_value(1)
        self.backup_schedule_view_cleanup_keep_yearly_row.set_range(0, 1000)
        self.backup_schedule_view_cleanup_keep_yearly_row.get_adjustment().set_step_increment(1)
        self.backup_schedule_view_cleanup.add(self.backup_schedule_view_cleanup_keep_yearly_row)
        def on_cleanup_keep_yearly_changed(switch, gparam):
            backup_store.get_backup_config(self.selected_id).schedule.cleanup_keep_yearly = switch.get_value()
        self.backup_schedule_view_cleanup_keep_yearly_row.connect("notify::value", on_cleanup_keep_yearly_changed)

        def on_cleanup_enabled_changed(switch, gparam):
            if "selcted_id" in self.__dict__:
                backup_store.get_backup_config(self.selected_id).schedule.cleanup_schedule_enabled = switch.get_active()
            self.backup_schedule_view_cleanup_keep_hourly_row.set_sensitive(switch.get_active())
            self.backup_schedule_view_cleanup_keep_daily_row.set_sensitive(switch.get_active())
            self.backup_schedule_view_cleanup_keep_weekly_row.set_sensitive(switch.get_active())
            self.backup_schedule_view_cleanup_keep_monthly_row.set_sensitive(switch.get_active())
            self.backup_schedule_view_cleanup_keep_yearly_row.set_sensitive(switch.get_active())

        on_cleanup_enabled_changed(self.backup_schedule_view_cleanup_enabled_row, None)
        self.backup_schedule_view_cleanup_enabled_row.connect("notify::active", on_cleanup_enabled_changed)

    def navigate_to(self, param, window):
        self.selected_id = param
        
        self.header = Gtk.HeaderBar()
        self.back_button = Gtk.Button(label="Back")
        def on_back_button_clicked(button):
            # save
            config.save_all_configs(self.backup_store)
            self.navigate_callback("main", None)
        self.back_button.connect("clicked", on_back_button_clicked)
        self.header.pack_start(self.back_button)
        window.set_titlebar(self.header)

        backup_schedule = self.backup_store.get_backup_config(self.selected_id).schedule
        if backup_schedule is None:
            return
        self.backup_schedule_view_backup_settings_allow_on_metered_row.set_active(backup_schedule.allow_on_metered)
        self.backup_schedule_view_preferences_on_connect_to_wifi_row.set_active(backup_schedule.on_network)
        self.backup_schedule_view_preferences_on_connect_to_power_row.set_active(backup_schedule.on_ac)
        self.backup_schedule_view_preferences_backup_enaled_row.set_active(backup_schedule.backup_schedule_enabled)
        self.backup_schedule_view_preferences_backup_frequency_row.set_selected(0 if backup_schedule.backup_frequency == "hourly" else (1 if backup_schedule.backup_frequency == "daily" else 2))
        self.backup_schedule_view_cleanup_enabled_row.set_active(backup_schedule.cleanup_schedule_enabled)
        self.backup_schedule_view_cleanup_keep_hourly_row.set_value(backup_schedule.cleanup_keep_hourly)
        self.backup_schedule_view_cleanup_keep_daily_row.set_value(backup_schedule.cleanup_keep_daily)
        self.backup_schedule_view_cleanup_keep_weekly_row.set_value(backup_schedule.cleanup_keep_weekly)
        self.backup_schedule_view_cleanup_keep_monthly_row.set_value(backup_schedule.cleanup_keep_monthly)
        self.backup_schedule_view_cleanup_keep_yearly_row.set_value(backup_schedule.cleanup_keep_yearly)
        self.backup_schedule_view_preferences_backup_frequency_row.set_subtitle("Every 24 hours" if backup_schedule.backup_frequency == "daily" else "Every 7 days" if backup_schedule.backup_frequency == "weekly" else "Every hour")

    