from gi.repository import Gtk, Adw, Gio, GObject
import components

class BackupEntry(GObject.Object):
  __gtype_name__ = 'BackupEntry'

  def __init__(self, name, backup_id, host):
    super().__init__()

    self._name = name
    self._id = backup_id
    self._host = host

  @GObject.Property(type=str)
  def name(self):
    return self._name


  @GObject.Property(type=int)
  def id(self):
    return self._id

  @GObject.Property(type=str)
  def host(self):
    return self._host
    


class HistoryView(Gtk.Box):
    def __init__(self, backup_store, navigate):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_store= backup_store
        self.navigate_callback = navigate
        
        filter_factory = Gtk.SignalListItemFactory()
        filter_factory.connect('setup', self.factory_setup)
        filter_factory.connect('bind', self.factory_bind)

        self.filter_model = Gio.ListStore(item_type=BackupEntry)

        self.listview = Gtk.ListView.new(factory=filter_factory, model=Gtk.MultiSelection.new(self.filter_model))
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_child(self.listview)
        scrolled_window.set_vexpand(True)
        scrolled_window.get_style_context().add_class("linked")
        self.append(scrolled_window)

        self.listview.connect("activate", self.on_selected)

    def on_selected(self, listview, index):
        model = self.listview.get_model()
        backup = model.get_item(index)
        self.navigate_callback("restore", (self.selected_id, backup.id))

    def factory_setup(self, factory, list_item):
        row = Adw.ActionRow()
        row.set_title("Backup")
        row.set_subtitle("Id")
        icon = components.StatusIcon()
        icon.set_icon("view-restore-symbolic", "primary")
        row.add_prefix(icon)
        row.set_activatable(True)
        label = Gtk.Label()
        label.set_text("Backup")
        label.get_style_context().add_class("primary-label")
        row.add_suffix(label)
        row.label = label
        list_item.set_child(row)

    def factory_bind(self, factory, list_item):
        row = list_item.get_child()
        row_item = list_item.get_item()
        row.set_title(row_item.name)
        row.set_subtitle(row_item.id)
        row.label.set_text(row_item.host)

    def navigate_to(self, param, window):
        self.selected_id = param
        self.header = Gtk.HeaderBar()
        self.back_button = Gtk.Button(label="Back")
        def back_button_clicked(button):
            self.navigate_callback("main", None)
        self.back_button.connect("clicked", lambda _: back_button_clicked(self.back_button))
        self.header.pack_start(self.back_button)
        window.set_titlebar(self.header)

        self.filter_model = Gio.ListStore(item_type=BackupEntry)

        backups = reversed(self.backup_store.get_backup_config(self.selected_id).status.backups)
        backups = list(backups)
        backups = filter(lambda x: ("tags" in x) and ("com.quexten.kinko" in x.get("tags")), backups)

        for backup in backups:
            self.filter_model.append(BackupEntry(backup.get("time").strftime("%Y-%m-%d %H:%M:%S"), backup.get("short_id"), backup.get("hostname")))
        self.listview.set_model(Gtk.SingleSelection.new(self.filter_model))
