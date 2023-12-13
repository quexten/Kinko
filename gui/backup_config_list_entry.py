from gi.repository import Gtk, Adw, Gdk, Graphene, Gsk, Gio, GLib, GObject
from datetime import datetime, timezone, timedelta
import timeago


def create_backup_preview_box(backup_config, view_details_callback=None, view_schedule_callback=None, view_backup_history_callback=None, show_edit_backup_dialog_callback=None):
    list = Gtk.ListBox()
    list.get_style_context().add_class("boxed-list")
    list.set_selection_mode(Gtk.SelectionMode.NONE)

    main_row = Adw.ActionRow()
    main_row.set_title("<b>" + backup_config.settings.name + "</b>")
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

    status_box_running = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    status_box_running.set_margin_start(10)
    status_box_running.set_margin_end(10)
    status_box_running.set_margin_top(10)
    status_box_running.set_margin_bottom(10)
    title = Gtk.Label(label="Backing up...")
    title.set_markup("<b>Backing up...</b>")
    title.set_halign(Gtk.Align.START)
    status_box_running.append(title)

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
    error_box.set_subtitle("Failed to backup")
    error_box.set_activatable(True)
    error_box.set_icon_name("dialog-error-symbolic")
    status_box.add_named(error_box, "error")

    last_backup_row = Adw.ActionRow()
    last_backup_row.set_title("Last Backup")
    last_backup_row.set_activatable(True)
    last_backup = backup_config.status.last_backup
    if last_backup is not None:
        last_backup_row.set_subtitle(timeago.format(last_backup, datetime.now(timezone.utc)))
    else:
        last_backup_row.set_subtitle("Never")
    last_backup_row.set_icon_name("emblem-default-symbolic")
    list.append(last_backup_row)

    schedule_row = Adw.ActionRow()
    schedule_row.set_title("Schedule")
    schedule_row.set_subtitle("Every 24 hours")
    schedule_row.set_activatable(True)
    schedule_row.set_icon_name("x-office-calendar-symbolic")
    list.append(schedule_row)

    def on_row_click(row, button):
        if button == main_row:
            if show_edit_backup_dialog_callback is not None:
                show_edit_backup_dialog_callback(backup_config.settings.id)
        if button == status_row:
            if view_details_callback is not None:
                view_details_callback(list, button, backup_config.settings.id)
        if button == schedule_row:
            if view_schedule_callback is not None:
                view_schedule_callback(list, button, backup_config.settings.id)
        if button == last_backup_row:
            if view_backup_history_callback is not None:
                view_backup_history_callback(list, button, backup_config.settings.id)

    list.connect("row-activated", on_row_click)

    list.destroyed = False
    def on_destroy():
        list.destroyed = True
    list.on_destroy = on_destroy
    list.last_status = "Idle"
    
    def update_gui():
        status = backup_config.status.status
        progress = backup_config.status.progress
        if status == "Idle" and list.last_status != "Idle":
            status_box.set_visible_child_name("idle")
        if status == "Running" and list.last_status != "Running":
            status_box.set_visible_child_name("running")
        if status == "Error" and list.last_status != "Error":
            status_box.set_visible_child_name("error")
        if status == "Running" and list.last_status == "Running":
            progress_bar.set_fraction(progress)
            progress_bar.set_text(str(round(progress * 100, 2))+ "%")

            if backup_config.status.seconds_remaining is not None:
                if backup_config.status.seconds_remaining > 60 * 60:
                    subtitle.set_text("{} hours, {} minutes remainaing".format(int(backup_config.status.seconds_remaining / 60 / 60), int(backup_config.status.seconds_remaining / 60 % 60)))
                elif backup_config.status.seconds_remaining > 60:
                    subtitle.set_text("{} minutes, {} seconds remainaing".format(int(backup_config.status.seconds_remaining / 60), int(backup_config.status.seconds_remaining % 60)))
                else:
                    subtitle.set_text("{} seconds remainaing".format(int(backup_config.status.seconds_remaining)))
        list.last_status = status

                        
        if not backup_config.schedule.backup_schedule_enabled:
            status_box_idle_description_label.set_text("Scheduled Backup disabled")
        else:
            if backup_config.status.last_backup is None:
                status_box_idle_description_label.set_text("No Upcoming Backup")
            else:
                next_backup_time = backup_config.status.last_backup + timedelta(hours=(1 if backup_config.schedule.backup_frequency == "hourly" else (24 if backup_config.schedule.backup_frequency == "daily" else 7 * 24)))
                status_box_idle_description_label.set_text("Upcoming Backup {}".format(timeago.format(next_backup_time, datetime.now(timezone.utc))))


        if not list.destroyed:
            GObject.timeout_add(100, update_gui)
    GObject.timeout_add(100, lambda: update_gui())
    return list
