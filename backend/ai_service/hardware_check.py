import sys
import os
import shutil
import platform

print("=== 1. PYTHON ===")
print("Python Executable:", sys.executable)
print("Python Version:", sys.version)

print("\n=== 2. PLATFORM & CPU ===")
print("System:", platform.system(), platform.release())
print("Machine / Arch:", platform.machine())
print("Processor:", platform.processor())
try:
    import os
    print("Logical CPU Cores:", os.cpu_count())
except Exception as e:
    print("CPU count error:", e)

print("\n=== 3. MEMORY (RAM) ===")
try:
    import ctypes
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    total_gb = stat.ullTotalPhys / (1024 ** 3)
    avail_gb = stat.ullAvailPhys / (1024 ** 3)
    print(f"Total Physical RAM: {total_gb:.2f} GB")
    print(f"Available Physical RAM: {avail_gb:.2f} GB ({stat.dwMemoryLoad}% in use)")
except Exception as e:
    print("Error querying RAM:", e)

print("\n=== 4. DISK SPACE ===")
for drive in ["C:\\"]:
    try:
        total, used, free = shutil.disk_usage(drive)
        print(f"Drive {drive} - Free: {free / (1024**3):.2f} GB / Total: {total / (1024**3):.2f} GB")
    except Exception as e:
        print(f"Error checking drive {drive}: {e}")

print("\n=== 5. GPU & CUDA CHECK ===")
try:
    import subprocess
    v_out = subprocess.check_output('powershell -Command "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"', shell=True, text=True).strip()
    print("Graphics Adapter(s):\n" + v_out)
except Exception as e:
    print("Error querying Video Controller:", e)

nvcc_path = shutil.which("nvcc")
nvidia_smi_path = shutil.which("nvidia-smi")
print("CUDA Compiler (nvcc):", nvcc_path or "NOT FOUND")
print("NVIDIA SMI:", nvidia_smi_path or "NOT FOUND")

print("\n=== 6. PYTHON PACKAGES ===")
for pkg in ["torch", "transformers", "accelerate", "llama_cpp", "huggingface_hub"]:
    try:
        mod = __import__(pkg)
        version = getattr(mod, "__version__", "installed")
        print(f"Package '{pkg}': {version}")
    except ImportError:
        print(f"Package '{pkg}': NOT INSTALLED")

print("\n=== 7. SYSTEM LLAMA.CPP BINARIES ===")
for b in ["llama-cli", "llama-server", "llama.cpp"]:
    path = shutil.which(b)
    print(f"Binary '{b}':", path or "NOT FOUND")
