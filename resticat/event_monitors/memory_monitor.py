import threading
import ctypes
import time

def malloc_trim():
    while True:
        try:
            ctypes.CDLL('libc.so.6').malloc_trim(0)
        except Exception as e:
            pass
        time.sleep(60)

thread = threading.Thread(target=malloc_trim)
thread.start()