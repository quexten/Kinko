"""
Script to set the status of the background process.
Run separately so that gtk dependencies don't stick around in memory.
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import GLib, Gio
import sys

def set_status(message):
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    proxy = Gio.DBusProxy.new_sync(
        bus,
        Gio.DBusProxyFlags.NONE,
        None,
        'org.freedesktop.portal.Desktop',
        '/org/freedesktop/portal/desktop',
        'org.freedesktop.portal.Background',
        None,
    )

    options = {
        'message': GLib.Variant('s', message),
    }

    try:
        request = proxy.SetStatus('(a{sv})', options)
        if request is None:
            raise Exception(
                "Setting background status failed"
            )
        print("Status set")
    except Exception as e:
        print(e)

if len(sys.argv) > 1:
    set_status(sys.argv[1])

loop = GLib.MainLoop()
loop.run()
