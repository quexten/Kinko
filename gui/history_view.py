from gi.repository import Gtk, Adw

class HistoryView(Gtk.Box):
    def __init__(self, backup_store, navigate):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_store= backup_store
        self.navigate_callback = navigate
        
        self.set_margin_start(80)
        self.set_margin_end(80)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        
        self.history_label = Gtk.Label(label="")
        self.history_label.set_markup("<b>History</b>")
        self.history_label.set_halign(Gtk.Align.START)
        self.append(self.history_label)

        self.history_list = Gtk.ListBox()
        self.history_list.get_style_context().add_class("boxed-list")
        self.history_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.history_list.connect("row-activated", lambda listbox, button: self.show_edit_backup_dialog(listbox, self.selected_id))
        self.append(self.history_list)

    def navigate_to(self, param, window):
        self.header = Gtk.HeaderBar()
        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect("clicked", lambda _: self.navigate_callback("main", None))
        self.header.pack_start(self.back_button)
        window.set_titlebar(self.header)

    def switch_to_backup_history(self, window, stack, switch_to_overview):
        # switch stack
        stack.set_visible_child(self.backup_history)

        # update header
        self.header = Gtk.HeaderBar()
        window.set_titlebar(self.header)
        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect("clicked", lambda _: switch_to_overview())
        self.header.pack_start(self.back_button)

        # update list
        while self.history_list.get_first_child() is not None:
            self.history_list.remove(self.history_list.get_first_child())
        backups = self.backup_store.get_backup_config(self.selected_id).status.backups
        for backup in reversed(backups):
            row = Adw.ActionRow()
            row.set_title(backup.get("time").strftime("%Y-%m-%d %H:%M:%S"))
            row.set_subtitle(backup.get("short_id"))
            row.set_icon_name("emblem-default-symbolic")
            self.history_list.append(row)