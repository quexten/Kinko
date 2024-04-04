import os
from gi.repository import Gtk

isflatpak = os.path.exists("/.flatpak-info")
pathprefix = "/app/bin/" if isflatpak else "./"

def load_template(path):
    builder = Gtk.Builder()
    builder.add_from_file(pathprefix + ".templates/" + path)
    return builder