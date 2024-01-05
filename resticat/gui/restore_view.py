from gi.repository import Gtk, Adw, GLib
from backend import restic
import os
import threading
import humanize
import polars as pl
import components

userdata_filter = [
    {
        "type": "userdata",
        "app": "Documents",
        "path": "Documents",
        "icon": "folder-documents-symbolic"
    },
    {
        "type": "userdata",
        "app": "Music",
        "path": "Music",
        "icon": "folder-music-symbolic"
    },
    {
        "type": "userdata",
        "app": "Pictures",
        "path": "Pictures",
        "icon": "folder-pictures-symbolic"
    },
    {
        "type": "userdata",
        "app": "Projects",
        "path": "projects",
        "icon": "folder-symbolic"
    },
    {
        "type": "userdata",
        "app": "Projects",
        "path": "Projects",
        "icon": "folder-symbolic"
    },
    {
        "type": "userdata",
        "app": "Go Sources",
        "path": "go/src",
        "icon": "folder-symbolic"
    }
]

config_filter = [
    {
        "type": "config",
        "app": "Rclone",
        "path": ".config/rclone/"
    },
    {
        "type": "config",
        "app": "Mpv",
        "path": ".config/mpv/"
    },
    {
        "type": "config",
        "app": "Goldwarden",
        "path": ".config/goldwarden.json"
    },
    {
        "type": "config",
        "app": "Evolution",
        "path": ".config/evolution/"
    },
    {
        "type": "config",
        "app": "SSH",
        "path": ".ssh/"
    },
    {
        "type": "config",
        "app": "Git",
        "path": ".gitconfig"
    },
    {
        "type": "config",
        "app": "i3",
        "path": ".config/i3/"
    },
    {
        "type": "config",
        "app": "VSCode",
        "path": ".config/Code/"
    }
]


def get_description(result):
    if result["type"] == "userdata":
        return f'{result["files"]} Files - {humanize.naturalsize(result["filesize"])}'
    elif result["type"] == "flatpak":
        return f'{result["app"]}'
    elif result["type"] == "config":
        return f'{result["path"]}'
    else:
        return ""

def process_files(data):
    (files, data_from_path_function) = data
    results = {}
    for file in files:
        result = data_from_path_function(file["path"])
        if result is not None:
            if result["app"] not in results:
                result["files"] = []
                result["filesize"] = 0
                result["active"] = True
                results[result["app"]] = result
            result = results[result["app"]]
            result["files"].append(file["path"])
            result["filesize"] += file["size"]
    return results

class RestoreView(Gtk.Box):
    def __init__(self, backup_store, backup_executor, navigate_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_store = backup_store
        self.backup_executor = backup_executor
        self.navigate_callback = navigate_callback

    def load(self, config_id, snapshot_id):
        # remove old widgets
        snapshot = None
        for sn in self.backup_store.get_backup_config(config_id).status.backups:
            if sn["short_id"] == snapshot_id:
                snapshot = sn
                break

        results = {
            "userdata": [],
            "flatpak": [],
            "config": [],
            "total_filesize": 0,
            "total_files": 0,
            "mountpoint": snapshot["paths"][0]
        }

        cfg = self.backup_store.get_backup_config(config_id)
        self.id = cfg.settings.id
        print("getting files for snapshot")
        files = restic.files_for_snapshot(cfg.settings.get_restic_repo(), cfg.settings.s3_access_key, cfg.settings.s3_secret_key, cfg.settings.repository_password, snapshot_id)
        print("got files for snapshot")

        # print("analyzing files")
        pl_files = pl.DataFrame(files)
        pl_files = pl_files.with_columns(pl.col("path").str.replace("/home/[a-zA-Z]*/", "").alias("relative_path")).filter(pl.col("type") == "file")
        results["total_filesize"] = pl_files.select(pl.sum("size")).to_dict()["size"][0]
        results["total_files"] = len(pl_files.to_dict()["path"])

        flatpak_apps = pl_files.with_columns(pl.col("relative_path").str.starts_with(".var/app/").alias("is_flatpak")).filter(pl.col("is_flatpak") == True)
        flatpak_apps = flatpak_apps.with_columns(pl.col("relative_path").str.split("/").apply(lambda x: x[2] if len(x) > 2 else None).alias("app")).filter(pl.col("type") == "file")
        flatpak_apps = flatpak_apps.group_by(pl.col("app")).agg(pl.sum("size").alias("size"), pl.count("path").alias("files"))
        flatpak_apps = flatpak_apps.with_columns((".var/app/" + pl.col("app") + "/").alias("app_path"))
        # print(flatpak_apps)

        userdata_table = pl.DataFrame(userdata_filter)
        userdata_tables = pl.concat([pl_files.with_columns(app_type=pl.lit(f["type"]), app=pl.lit(f["app"]), app_path=pl.lit(f["path"]), icon=pl.lit(f["icon"])) for f in userdata_filter])
        userdata_tables = userdata_tables.with_columns(pl.col("relative_path").str.starts_with(userdata_tables["app_path"]).alias("is_userdata")).filter(pl.col("is_userdata") == True).filter(pl.col("type") == "file")
        number_of_userdata_files = len(userdata_tables.to_dict()["path"])
        size_of_userdata_files = userdata_tables.select(pl.sum("size")).to_dict()["size"][0]
        userdata_tables = userdata_tables.group_by(pl.col("app_type"), pl.col("app"), pl.col("app_path"), pl.col("icon")).agg(pl.sum("size").alias("size"), pl.count("path").alias("files"))
        # print(userdata_tables)

        config_tables = pl.concat([pl_files.with_columns(app_type=pl.lit(f["type"]), app=pl.lit(f["app"]), app_path=pl.lit(f["path"]), icon=None) for f in config_filter])
        config_tables = config_tables.with_columns(pl.col("relative_path").str.starts_with(config_tables["app_path"]).alias("is_config")).filter(pl.col("is_config") == True).filter(pl.col("type") == "file")
        number_of_config_files = len(config_tables.to_dict()["path"])
        size_of_config_files = config_tables.select(pl.sum("size")).to_dict()["size"][0]
        config_tables = config_tables.group_by(pl.col("app_type"), pl.col("app"), pl.col("app_path")).agg(pl.sum("size").alias("size"), pl.count("path").alias("files"))

        for row in userdata_tables.rows(named=True):
            results["userdata"].append({
                "type": row["app_type"],
                "app": row["app"],
                "path": row["app_path"],
                "full_path": "/" + row["app_path"],
                "icon": row["icon"],
                "files": row["files"],
                "filesize": row["size"],
                "active": True
            })
        for row in config_tables.rows(named=True):
            results["config"].append({
                "type": row["app_type"],
                "app": row["app"],
                "path": row["app_path"],
                "full_path": "/" + row["app_path"],
                "icon": None,
                "files": row["files"],
                "filesize": row["size"],
                "active": True
            })
        for row in flatpak_apps.rows(named=True):
            results["flatpak"].append({
                "type": "flatpak",
                "app": row["app"],
                "path": "~/.var/app/" + row["app"] + "/",
                "full_path": "/" + ".var/app/" + row["app"] + "/",
                "icon": None,
                "files": row["files"],
                "filesize": row["size"],
                "active": True
            })

        userdata_tables = None
        config_tables = None
        flatpak_apps = None

        GLib.idle_add(self.display_ui, snapshot_id, snapshot, results)

    def display_ui(self, snapshot_id, snapshot, results):
        firstchild = self.get_first_child()
        while self.get_first_child() is not None:
            self.remove(self.get_first_child())

        self.preferences_page = Adw.PreferencesPage()
        self.append(self.preferences_page)

        self.title_group = Adw.PreferencesGroup()
        self.title_group.set_title(f'Snapshot - {snapshot_id}')
        self.title_group.set_description(snapshot["time"].strftime("%Y-%m-%d %H:%M:%S") + " - " + str(results["total_files"]) + " Files - " + humanize.naturalsize(results["total_filesize"]))
        self.preferences_page.add(self.title_group)

        self.title_icon = components.StatusIcon()
        self.title_icon.set_icon("view-restore-symbolic", "primary")
        self.title_group.set_header_suffix(self.title_icon)

        self.userdata_group = Adw.PreferencesGroup()
        self.userdata_group.set_title("User Data")
        self.preferences_page.add(self.userdata_group)

        for result in results["userdata"]:
            row = Adw.SwitchRow()
            row.set_title(result["app"])
            row.set_subtitle(get_description(result))
            row.set_active(True)
            row.set_icon_name(result["icon"])
            def on_change_userdata(row, value):
                id = row.get_title()
                value = row.get_active()
                list(filter(lambda x: x["app"] == id, results["userdata"]))[0]["active"] = value
            row.connect("notify::active", lambda row, a: on_change_userdata(row, a))
            self.userdata_group.add(row)

        self.flatpak_group = Adw.PreferencesGroup()
        self.flatpak_group.set_title("Flatpak Application Data")
        self.preferences_page.add(self.flatpak_group)

        self.config_group = Adw.PreferencesGroup()
        self.config_group.set_title("Non-Sandboxed Application Data")
        self.preferences_page.add(self.config_group)
    
            
        for result in results["flatpak"]:
            row = Adw.SwitchRow()
            row.set_title(result["app"])
            row.set_subtitle(result["path"])
            row.set_active(True)
            row.get_style_context().add_class("suggested-action")
            # on change
            def on_change_flatpak(row, value):
                id = row.get_title()
                value = row.get_active()
                list(filter(lambda x: x["app"] == id, results["flatpak"]))[0]["active"] = value
                
            row.connect("notify::active", lambda row, a: on_change_flatpak(row, a))
            self.flatpak_group.add(row)

        for result in results["config"]:
            row = Adw.SwitchRow()
            row.set_title(result["app"])
            row.set_subtitle(get_description(result))
            row.set_active(True)
            row.get_style_context().add_class("suggested-action")
            def on_change(row, value):
                id = row.get_title()
                value = row.get_active()
                list(filter(lambda x: x["app"] == id, results["config"]))[0]["active"] = value
            row.connect("notify::active", lambda row, a: on_change(row, a))
            self.config_group.add(row)

        self.button_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.button_row.set_halign(Gtk.Align.CENTER)
        self.button_row.set_valign(Gtk.Align.CENTER)
        self.append(self.button_row)

        self.button = Gtk.Button(label="Restore to Home")
        self.button.get_style_context().add_class("suggested-action")
        self.button.connect("clicked", lambda _: self.restore(results, snapshot_id, snapshot["paths"][0]))
        # self.button.set_margin_start(160)
        self.button.set_margin_top(10)
        self.button.set_margin_bottom(10)
        self.button_row.append(self.button)

        self.restore_to_button = Gtk.Button(label="Restore to...")
        def restore_to():
            self.results = results
            self.snapshot_id = snapshot_id
            self.show_open_dialog(self.window)
        self.restore_to_button.connect("clicked", lambda _: restore_to())
        # self.button.set_margin_start(160)
        self.restore_to_button.set_margin_top(10)
        self.restore_to_button.set_margin_bottom(10)
        self.button_row.append(self.restore_to_button)

    
    def show_open_dialog(self, window):
        self.open_dialog = Gtk.FileChooserNative.new(title="Import Config", parent=window, action=Gtk.FileChooserAction.SELECT_FOLDER)
        self.open_dialog.connect("response", self.open_response)
        self.open_dialog.show()
    
    def open_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            filename = file.get_path()
            self.restore(self.results, self.snapshot_id, self.results["mountpoint"], filename)

    def navigate_to(self, param, window):
        self.window = window
        while self.get_first_child() is not None:
            self.remove(self.get_first_child())
        # add loading spinner
        self.loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.loading_box.set_halign(Gtk.Align.CENTER)
        self.loading_box.set_valign(Gtk.Align.CENTER)
        self.loading_box.set_vexpand(True)
        self.append(self.loading_box)
        self.loading_label = Gtk.Label(label="Loading...")
        self.loading_label.set_halign(Gtk.Align.CENTER)
        self.loading_label.set_valign(Gtk.Align.CENTER)
        self.loading_label.set_hexpand(True)
        self.loading_label.set_vexpand(True)
        self.loading_label.get_style_context().add_class("title-1")
        self.loading_box.append(self.loading_label)

        config_id, snapshot_id = param

        thread = threading.Thread(target=self.load, args=(config_id, snapshot_id))
        thread.start()

    def restore(self, results, snapshot, mountpoint, destination=None):
        if destination is None:
            destination = os.path.expanduser('~')

        paths = []
        for key in ["userdata", "flatpak", "config"]:
            for result in results[key]:
                if result["active"]:
                    paths.append(result["full_path"])
        if len(paths) == 0:
            return

        self.backup_executor.restore_now(self.id, snapshot, mountpoint, paths, [], destination)
        self.navigate_callback("main", None)