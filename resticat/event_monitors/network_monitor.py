import gi.repository.Gio as Gio
import time
import threading

last_status = None
last_status_time = None

def start_monitor(backup_executor):
    print("Starting network monitor...")

    def notify_thread():
        global last_status
        global last_status_time

        while True:
            if not last_status_time is None and time.time() - last_status_time > 5:
                if last_status == "metered":
                    backup_executor.notify("network_connected_metered")
                elif last_status == "unmetered":
                    backup_executor.notify("network_connected_unmetered")
                else:
                    backup_executor.notify("network_disconnected")
                last_status_time = None
            time.sleep(1)
    
    def network_status_changed(monitor, connected):
        global last_status
        global last_status_time

        metered = monitor.get_network_metered()
        if connected:
            if metered:
                last_status = "metered"
            else:
                last_status = "unmetered"
        else:
            last_status = "disconnected"
        last_status_time = time.time()

    thread = threading.Thread(target=notify_thread, args=())
    thread.start()

    network_monitor = Gio.NetworkMonitor.get_default()
    network_monitor.connect('network-changed', network_status_changed)
    status = network_monitor.get_network_metered()
    network_status_changed(network_monitor, status)