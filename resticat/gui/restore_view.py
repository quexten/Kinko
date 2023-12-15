from gi.repository import Gtk, Adw, Gdk, Graphene, Gsk, Gio, GLib, GObject
import backend.config as config
from backend import restic

def userdata_filter(path):
    if path.startswith("Documents"):
        return {
            "type": "userdata",
            "app": "Documents",
            "path": "Documents"
        }
    elif path.startswith("Music"):
        return {
            "type": "userdata",
            "app": "Music",
            "path": "Music"
        }
    elif path.startswith("Pictures"):
        return {
            "type": "userdata",
            "app": "Pictures",
            "path": "Pictures"
        }
    else:
        return None

def flatpak_data_filter(path):
    if ".var/app" in path:
        # extract app id
        try:
            app = path.split(".var/app/")[1].split("/")[0]
            return {
                "type": "flatpak",
                "app": app,
                "path": ".var/app/" + app + "/"
            }
        except:
            return None
    else:
        return None

def config_filter(path):
    if path == ".config/rclone/rclone.conf":
        return {
            "type": "config",
            "app": "rclone",
            "path": ".config/rclone/"
        }
    elif path == ".config/mpv/mpv.conf":
        return {
            "type": "config",
            "app": "mpv",
            "path": ".config/mpv/"
        }
    elif path == ".config/goldwarden.json":
        return {
            "type": "config",
            "app": "goldwarden",
            "path": ".config/goldwarden.json"
        }
    elif path.startswith(".config/evolution"):
        return {
            "type": "config",
            "app": "evolution",
            "path": ".config/evolution/"
        }
    elif path.startswith(".ssh/"):
        return {
            "type": "config",
            "app": "ssh",
            "path": ".ssh/"
        }
    elif path.startswith(".gitconfig"):
        return {
            "type": "config",
            "app": "git",
            "path": ".gitconfig"
        }
    elif path.startswith(".config/i3/config"):
        return {
            "type": "config",
            "app": "i3",
            "path": ".config/i3/"
        }
    elif path.startswith(".config/Code"):
        return {
            "type": "config",
            "app": "vscode",
            "path": ".config/Code/"
        }
    
    else:
        return None

def userdata_filter(path):
    if "Documents" in path:
        return {
            "type": "userdata",
            "app": "Documents",
            "path": "Documents"
        }
    elif "Music" in path:
        return {
            "type": "userdata",
            "app": "Music",
            "path": "Music"
        }
    elif "Pictures" in path:
        return {
            "type": "userdata",
            "app": "Pictures",
            "path": "Pictures"
        }
    else:
        return None

filters = [flatpak_data_filter, config_filter, userdata_filter]

def get_description(result):
    if result["type"] == "userdata":
        return f'{result["app"]} ({len(result["files"])}) Files'
    elif result["type"] == "flatpak":
        return f'{result["app"]}'
    elif result["type"] == "config":
        return f'{result["app"]}'
    else:
        return ""

class RestoreView(Gtk.Box):
    def __init__(self, backup_store, backup_executor, navigate_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.backup_store = backup_store
        self.backup_executor = backup_executor
        self.navigate_callback = navigate_callback

    def navigate_to(self, param, window):
        # remove old widgets
        firstchild = self.get_first_child()
        while self.get_first_child() is not None:
            self.remove(self.get_first_child())

        results = {
            "userdata": [],
            "flatpak": [],
            "config": [],
        }

        cfg = self.backup_store.get_backup_configs()[1]
        self.id = cfg.settings.id
        print("getting files for snapshot")
        files = restic.files_for_snapshot(cfg.settings.aws_s3_repository, cfg.settings.aws_s3_access_key, cfg.settings.aws_s3_secret_key, cfg.settings.repository_password, "latest")
        print("got files for snapshot")

        print("analyzing files")
        for file in files:
            path = file["path"].replace("/home/quexten/", "")
            for f in filters:
                result = f(path)
                if result is not None:
                    result_list = results[result["type"]]
                    result["active"] = True
                    if len(list(filter(lambda x: x["app"] == result["app"], result_list))) == 0:
                        result["files"] = []
                        if file["type"] == "file":
                            result["files"].append(path)
                        result_list.append(result)
                    else:
                        if file["type"] == "file":
                            list(filter(lambda x: x["app"] == result["app"], result_list))[0]["files"].append(path)
                    break
        print("analyzed files")

        self.preferences_page = Adw.PreferencesPage()
        self.append(self.preferences_page)

        self.userdata_group = Adw.PreferencesGroup()
        self.userdata_group.set_title("User Data")
        self.preferences_page.add(self.userdata_group)

        for result in results["userdata"]:
            row = Adw.SwitchRow()
            row.set_title(result["app"])
            row.set_subtitle(get_description(result))
            row.set_active(True)
            row.set_icon_name("folder-documents-symbolic")
            def on_change_userdata(row, value):
                id = row.get_title()
                value = row.get_active()
                result["active"] = value
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

        self.button = Gtk.Button(label="Restore")
        self.button.get_style_context().add_class("suggested-action")
        self.button.connect("clicked", lambda _: self.restore(results))
        self.button.set_margin_start(160)
        self.button.set_margin_end(160)
        self.append(self.button)
    
    def restore(self, results):
        paths = []
        for key in results:
            for result in results[key]:
                if result["active"]:
                    paths.append("/home/quexten" + "/" + result["path"])
        if len(paths) == 0:
            return

        self.backup_executor.restore_now(self.id, "latest", paths)
        self.navigate_callback("main", None)