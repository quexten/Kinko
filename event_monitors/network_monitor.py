import gi.repository.Gio as Gio

def start_monitor(backup_executor):
    print("Starting network monitor...")
    def network_status_changed(monitor, connected):
        metered = monitor.get_network_metered()
        if connected:
            if metered:
                backup_executor.notify("network_connected_metered")
            else:
                backup_executor.notify("network_connected_unmetered")
        else:
            backup_executor.notify("network_disconnected")

    network_monitor = Gio.NetworkMonitor.get_default()
    network_monitor.connect('network-changed', network_status_changed)