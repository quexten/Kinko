
import threading
import time

def start_monitor(backup_executor):
    print("Starting power monitor...")
    def monitor_power():
        last = None
        while True:
            with open("/sys/class/power_supply/BAT0/status", "r") as f:
                status = f.read()
                if status == "Discharging\n":
                    if last != "Discharging" and last is not None:
                        backup_executor.notify("power_off")
                    last = "Discharging"
                else:
                    if last != "Charging" and last is not None:
                        backup_executor.notify("power_on")
                    last = "Charging"
            time.sleep(1)
    power_thread = threading.Thread(target=monitor_power, args=())
    power_thread.daemon = True
    power_thread.start()
