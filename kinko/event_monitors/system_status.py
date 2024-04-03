import threading
import time
import gi.repository.Gio as Gio
from enum import Enum

class PowerSaverStatus(Enum):
    Enabled = 1
    Disabled = 2

class NetworkStatus(Enum):
    DISCONNECTED = 1
    METERED = 2
    UNMETERED = 3

class SystemStatus():
    def __init__(self):
        self.network_status = NetworkStatus.DISCONNECTED
        self.power_saver_status = PowerSaverStatus.Disabled

        self.last_network_status = None
        self.last_status_time = None

        self.start_monitors()

    def start_monitors(self):
        self.start_powersaver_monitor()
        self.start_network_monitor()

    def get_network_status(self):
        return self.network_status

    def get_power_saver_status(self):
        return self.power_saver_status    

    def start_network_monitor(self):
        print("Starting network monitor...")

        def notify_thread():
            while True:
                if not self.last_status_time is None and time.time() - self.last_status_time > 5:
                    if self.last_network_status == "metered":
                        self.network_status = NetworkStatus.METERED
                    elif self.last_network_status == "unmetered":
                        self.network_status = NetworkStatus.UNMETERED    
                    else:
                        self.network_status = NetworkStatus.DISCONNECTED
                    self.last_status_time = None
                time.sleep(1)
        
        def network_status_changed(monitor, conn):
            metered = monitor.get_network_metered()
            connected = monitor.get_connectivity() == Gio.NetworkConnectivity.FULL

            if connected:
                if metered:
                    self.last_network_status = "metered"
                else:
                    self.last_network_status = "unmetered"
            else:
                self.last_network_status = "disconnected"
            print("Network status changed", self.last_network_status)
            self.last_status_time = time.time()

        thread = threading.Thread(target=notify_thread, args=())
        thread.start()

        network_monitor = Gio.NetworkMonitor.get_default()
        network_monitor.connect('network-changed', network_status_changed)
        status = network_monitor.get_network_metered()
        network_status_changed(network_monitor, status)

    def start_powersaver_monitor(self):
        print("Starting power-profile monitor...")
        def power_profile_status_changed(obj, pspec):
            power_save_enabled = self.power_profile_monitor.get_power_saver_enabled()
            self.power_saver_status = PowerSaverStatus.Enabled if power_save_enabled else PowerSaverStatus.Disabled

        self.power_profile_monitor = Gio.PowerProfileMonitor.dup_default()
        self.power_saver_status = self.power_profile_monitor.get_power_saver_enabled()
        self.power_profile_monitor.connect(
            'notify::power-saver-enabled', power_profile_status_changed
        )