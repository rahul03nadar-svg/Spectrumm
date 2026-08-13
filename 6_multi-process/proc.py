import ctypes
import sys
import time

SHM_INPUT_KEY = 0x1234
SHM_OUTPUT_KEY = 0x5678
CHANNELS = 1024
WINDOW_SIZE = 5
INTERVAL = 0.016

class SpectrumData(ctypes.Structure):
    _fields_ = [("active", ctypes.c_int), ("data", ctypes.c_float * CHANNELS)]

libc = ctypes.CDLL("libc.so.6")
libc.shmget.argtypes = [ctypes.c_int, ctypes.c_size_t, ctypes.c_int]
libc.shmget.restype = ctypes.c_int
libc.shmat.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
libc.shmat.restype = ctypes.c_void_p
libc.shmdt.argtypes = [ctypes.c_void_p]
libc.shmdt.restype = ctypes.c_int

def connect_shared_memory(key, create=False):
    flags = 0o666
    if create: flags |= 0o1000
    shmid = libc.shmget(key, ctypes.sizeof(SpectrumData), flags)
    if shmid < 0: return None, None
    ptr = libc.shmat(shmid, None, 0)
    if ptr is None or ptr == ctypes.c_void_p(-1).value: return None, None
    shared = ctypes.cast(ptr, ctypes.POINTER(SpectrumData))
    return shmid, (ptr, shared)

def moving_average(data):
    result = [0.0] * CHANNELS
    half = WINDOW_SIZE // 2
    for i in range(CHANNELS):
        start = max(0, i - half)
        end = min(CHANNELS, i + half + 1)
        result[i] = sum(data[start:end]) / (end - start)
    return result

def main():
    print("Data Processor starting...")
    input_shmid, input_mem = connect_shared_memory(SHM_INPUT_KEY)
    if input_mem is None:
        print("Error: Generator shared memory not found.")
        print("Start spectrum_generator first.")
        sys.exit(1)
    output_shmid, output_mem = connect_shared_memory(SHM_OUTPUT_KEY, create=True)
    if output_mem is None:
        print("Error: Could not create output shared memory.")
        libc.shmdt(input_mem[0])
        sys.exit(1)
    input_ptr, input_shared = input_mem
    output_ptr, output_shared = output_mem
    output_shared.contents.active = 1
    print("Processor connected.")
    print("Moving average window:", WINDOW_SIZE)
    try:
        while True:
            if input_shared.contents.active == 1:
                data = list(input_shared.contents.data)
                smoothed = moving_average(data)
                for i in range(CHANNELS): output_shared.contents.data[i] = smoothed[i]
                output_shared.contents.active = 1
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nProcessor stopped.")
    except Exception as e:
        print("Processor error:", e)
    finally:
        output_shared.contents.active = 0
        libc.shmdt(input_ptr)
        libc.shmdt(output_ptr)

if __name__ == "__main__":
    main()
