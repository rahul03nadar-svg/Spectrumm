import ctypes
import os
import struct
import sys
import time

SHM_KEY = 0x1234
CHANNELS = 1024
OUTPUT_FILE = "../data/spectrum.bin"
INTERVAL = 0.1

try:
    libc = ctypes.CDLL("libc.so.6")
except OSError as e:
    print(f"Error loading libc: {e}")
    sys.exit(1)

libc.shmget.argtypes = [ctypes.c_int, ctypes.c_size_t, ctypes.c_int]
libc.shmget.restype = ctypes.c_int
libc.shmat.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
libc.shmat.restype = ctypes.c_void_p
libc.shmdt.argtypes = [ctypes.c_void_p]
libc.shmdt.restype = ctypes.c_int

def connect_shared_memory():
    size = 4 + CHANNELS * 4
    shmid = libc.shmget(SHM_KEY, size, 0o666)
    if shmid < 0:
        print("Error: Shared memory not found. Start C generator first.")
        sys.exit(1)
    ptr = libc.shmat(shmid, None, 0)
    if ptr is None or ptr == ctypes.c_void_p(-1).value:
        print("Error: Failed to attach shared memory.")
        sys.exit(1)
    return ptr

def read_active(ptr):
    return ctypes.cast(ptr, ctypes.POINTER(ctypes.c_int)).contents.value

def read_spectrum(ptr):
    address = ptr + 4
    data = ctypes.cast(address, ctypes.POINTER(ctypes.c_float * CHANNELS))
    return list(data.contents)

def main():
    ptr = connect_shared_memory()
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    frame = 0
    print("Binary Logger started.")
    print(f"Saving data")
    print("Press Ctrl+C to stop.")
    try:
        with open(OUTPUT_FILE, "wb") as file:
            while True:
                if read_active(ptr):
                    spectrum = read_spectrum(ptr)
                    file.write(struct.pack("I", frame))
                    file.write(struct.pack("d", time.time()))
                    file.write(struct.pack(f"{CHANNELS}f", *spectrum))
                    file.flush()
                    frame += 1
                    if frame % 100 == 0:
                        print(f"Recorded spectra: {frame}")
                time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nLogger stopped.")
    except Exception as e:
        print(f"Logger error: {e}")
    finally:
        libc.shmdt(ptr)
        print(f"Total spectra recorded: {frame}")

if __name__ == "__main__":
    main()
