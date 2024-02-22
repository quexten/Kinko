import threading
import time
import gi.repository.Gio as Gio

power_monitor = None

def notify_power_profile(executor, power_save_enabled):
    print("power save enabled:", power_save_enabled)
    if power_save_enabled:
        executor.notify("power_profile_low")
    else:
        executor.notify("power_profile_high")


def start_monitor(backup_executor):
    global power_profile_monitor

    print("Starting battery monitor...")
    def monitor_power():
        last = None
        while True:
            with open("/sys/class/power_supply/BAT0/status", "r") as f:
                status = f.read().strip()
                if status != last:
                    last = status
                    print("battery status:", status)
                    message = "power_off" if status == "Discharging" else "power_on"
                    backup_executor.notify(message)

            time.sleep(1)
    power_thread = threading.Thread(target=monitor_power, args=())
    power_thread.daemon = True
    power_thread.start()

    print("Starting power-profile monitor...")
    def power_profile_status_changed(obj, pspec):
        global power_profile_monitor
        power_save_enabled = power_profile_monitor.get_power_saver_enabled()
        notify_power_profile(backup_executor, power_save_enabled)

    power_profile_monitor = Gio.PowerProfileMonitor.dup_default()
    notify_power_profile(backup_executor, power_profile_monitor.get_power_saver_enabled())
    power_profile_monitor.connect(
        'notify::power-saver-enabled', power_profile_status_changed
    )