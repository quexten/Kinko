from gi.repository import Gtk, Adw, GObject
from datetime import datetime, timezone, timedelta
import timeago
import ipc
import components

class MainView(Gtk.Box):
    def __init__(self, b, be, navigate_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_margin_start(80)
        self.set_margin_end(80)
        self.backup_store = b
        self.backup_executor = be
        self.navigate_callback = navigate_callback
        self.number_of_rendered_children = 0
        GObject.timeout_add(100, lambda: self.tick())

    def navigate_to(self, param, window):
        self.header = Gtk.HeaderBar()
        self.back_button = Gtk.Button(label="Add Backup")
        self.back_button.get_style_context().add_class("suggested-action")
        self.back_button.connect("clicked", lambda _: self.navigate_callback("edit", None))
        self.header.pack_start(self.back_button)
        window.set_titlebar(self.header)
        self.render_list()

    def render_list(self):
        while self.get_first_child() is not None:
            self.get_first_child().on_destroy()
            self.remove(self.get_first_child())

        self.number_of_rendered_children = 0
        for backup_config in self.backup_store.get_backup_configs():
            self.append(self.create_backup_preview_box(backup_config, self.navigate_callback))
            self.number_of_rendered_children += 1

    def tick(self):
        # check number of children
        if self.number_of_rendered_children != len(self.backup_store.get_backup_configs()):
            self.render_list()
        GObject.timeout_add(100, lambda: self.tick())

    def create_backup_preview_box(self, backup_config, navigate_callback):
        list = Gtk.ListBox()
        list.set_margin_top(20)
        list.get_style_context().add_class("boxed-list")
        list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.backup_config = backup_config

        main_row = Adw.ActionRow()
        main_row.set_title("<b>" + self.backup_config.settings.name + "</b>")
        main_row.set_subtitle("S3 Destination")
        main_row.set_activatable(True)
        main_row.get_style_context().add_class("suggested-action")
        #pencile
        main_row.add_suffix(Gtk.Image.new_from_icon_name("document-edit-symbolic"))

        list.append(main_row)

        status_row = Gtk.ListBoxRow()
        status_row.set_selectable(False)
        list.append(status_row)

        status_box = Gtk.Stack()
        status_box.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        status_box.set_transition_duration(200)
        status_row.set_child(status_box)

        status_box_idle = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box_idle.set_margin_start(10)
        status_box_idle.set_margin_end(10)
        status_box_idle.set_margin_top(10)
        status_box_idle.set_margin_bottom(10)
        title = Gtk.Label(label="Idle")
        title.set_markup("<b>Idle</b>")
        title.set_halign(Gtk.Align.START)
        status_box_idle.append(title)
        status_box_idle_description_label = Gtk.Label(label="Upcoming Backup - 12:00")
        status_box_idle_description_label.set_halign(Gtk.Align.START)
        status_box_idle_description_label.get_style_context().add_class("dim-label")
        status_box_idle.append(status_box_idle_description_label)
        status_box.add_named(status_box_idle, "idle")

        status_box_running_cleanup = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box_running_cleanup.set_margin_start(10)
        status_box_running_cleanup.set_margin_end(10)
        status_box_running_cleanup.set_margin_top(10)
        status_box_running_cleanup.set_margin_bottom(10)
        running_cleanup_title = Gtk.Label(label="Cleaning up...")
        running_cleanup_title.set_markup("<b>Cleaning up...</b>")
        running_cleanup_title.set_halign(Gtk.Align.START)
        status_box_running_cleanup.append(running_cleanup_title)
        status_box.add_named(status_box_running_cleanup, "running-cleanup")

        status_box_running = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_box_running.set_margin_start(10)
        status_box_running.set_margin_end(10)
        status_box_running.set_margin_top(10)
        status_box_running.set_margin_bottom(10)
        running_title = Gtk.Label(label="Backing up...")
        running_title.set_markup("<b>Backing up...</b>")
        running_title.set_halign(Gtk.Align.START)
        status_box_running.append(running_title)

        subtitle = Gtk.Label(label="Calculating time remaining")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.get_style_context().add_class("dim-label")
        status_box_running.append(subtitle)

        progress_bar = Gtk.ProgressBar()
        progress_bar.set_show_text(False)
        progress_bar.set_fraction(0)
        progress_bar.set_hexpand(True)
        progress_bar.set_margin_end(10)
        status_box_running.append(progress_bar)
        status_box.add_named(status_box_running, "running")

        error_box = Adw.ActionRow()
        error_box.set_title("Error")
        error_box.set_subtitle("An error occured")
        error_box.set_activatable(True)
        error_box.set_icon_name("dialog-error-symbolic")
        status_box.add_named(error_box, "error")

        last_backup_row = Adw.ActionRow()
        last_backup_row.set_title("Last Backup")
        last_backup_row.set_activatable(True)
        last_backup = self.backup_config.status.last_backup
        if last_backup is not None:
            last_backup_row.set_subtitle(timeago.format(last_backup, datetime.now(timezone.utc)))
        else:
            last_backup_row.set_subtitle("Never")
        last_backup_icon = components.StatusIcon()
        last_backup_icon.set_icon("emblem-default-symbolic", "ok")
        last_backup_row.add_prefix(last_backup_icon)
        list.append(last_backup_row)

        schedule_row = Adw.ActionRow()
        schedule_row.set_title("Schedule")
        schedule_row.set_subtitle("Every 24 hours")
        schedule_row.set_activatable(True)
        schedule_row.set_icon_name("x-office-calendar-symbolic")
        list.append(schedule_row)

        def on_row_click(row, button):
            if button == main_row:
                navigate_callback("edit", self.backup_config.settings.id)
            if button == status_row:
                navigate_callback("status", self.backup_config.settings.id)
            if button == schedule_row:
                navigate_callback("schedule", self.backup_config.settings.id)
            if button == last_backup_row:
                if self.backup_config.status.last_backup is not None:
                    navigate_callback("history", self.backup_config.settings.id)

        list.connect("row-activated", on_row_click)

        list.destroyed = False
        def on_destroy():
            list.destroyed = True
        list.on_destroy = on_destroy

        list.last_status = self.backup_config.status.status
        status_box.set_transition_duration(0)
        status_box.set_visible_child_name(backup_config.status.status.lower())
        status_box.set_transition_duration(200)

        def update_gui():
            self.backup_config = self.backup_store.get_backup_config(backup_config.settings.id)
            status = self.backup_config.status.status
            progress = self.backup_config .status.progress
            running_title.set_text(backup_config.status.message)
            schedule_row.set_subtitle("Every 24 hours" if self.backup_config.schedule.backup_frequency == "daily" else "Every 7 days" if self.backup_config.schedule.backup_frequency == "weekly" else "Every hour")
            last_backup = self.backup_config.status.last_backup
            if last_backup is not None:
                backups = self.backup_config.status.backups
                timeago_string = timeago.format(last_backup, datetime.now(timezone.utc))
                last_backup_row.set_subtitle(f'{timeago_string}')
            else:
                last_backup_row.set_subtitle("Never")
            if status == "Idle" and list.last_status != "Idle":
                status_box.set_visible_child_name("idle")
            if status == "Running-Cleanup" and list.last_status != "Running-Cleanup":
                status_box.set_visible_child_name("running-cleanup")
            if status == "Running" and list.last_status != "Running":
                status_box.set_visible_child_name("running")
            if status == "Error" and list.last_status != "Error":
                status_box.set_visible_child_name("error")
            if status == "Running" and list.last_status == "Running":
                progress_bar.set_fraction(progress)
                progress_bar.set_text(str(round(progress * 100, 2))+ "%")

                if self.backup_config.status.seconds_remaining is not None:
                    if self.backup_config.status.seconds_remaining > 60 * 60:
                        subtitle.set_text("{} hours, {} minutes remainaing".format(int(self.backup_config.status.seconds_remaining / 60 / 60), int(backup_config.status.seconds_remaining / 60 % 60)))
                    elif self.backup_config.status.seconds_remaining > 60:
                        subtitle.set_text("{} minutes remainaing".format(int(self.backup_config.status.seconds_remaining / 60)))
                    else:
                        subtitle.set_text("{} seconds remainaing".format(int(self.backup_config.status.seconds_remaining)))
            list.last_status = status

                            
            if not self.backup_config.schedule.backup_schedule_enabled:
                status_box_idle_description_label.set_text("Scheduled Backup disabled")
            else:
                if self.backup_config.status.last_backup is None:
                    status_box_idle_description_label.set_text("No Upcoming Backup")
                else:
                    next_backup = self.backup_executor.get_next_backup_time(self.backup_config.settings.id)
                    if next_backup == "powersaver":
                        status_box_idle_description_label.set_text("Backup disabled due to power saving")
                    elif next_backup == "battery":
                        status_box_idle_description_label.set_text("Backup disabled due to battery")
                    elif next_backup == "metered":
                        status_box_idle_description_label.set_text("Backup disabled due to metered connection")
                    else:
                        status_box_idle_description_label.set_text("Upcoming Backup {}".format(next_backup))


            if not list.destroyed:
                GObject.timeout_add(1000, update_gui)
        GObject.timeout_add(50, lambda: update_gui())
        return list
