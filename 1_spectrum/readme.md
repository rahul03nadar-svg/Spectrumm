# 1 – Real-Time Spectrum Generator

# Objective
Develop two applications: a C program that continuously generates random spectrum data for 1024 channels and writes it into Linux shared memory, and a Python PyQt5 application that reads the shared memory and displays a live-updating spectrum.

# Architecture

C Spectrum Generator -> Linux Shared Memory -> Python PyQt5 Viewer -> Live Spectrum Graph

## Technologies
- C / GCC
- Ubuntu 22.04+
- Linux shared memory
- Python 3
- PyQt5
- PyQtGraph
- NumPy
- ctypes

## Features
- 1024-channel spectrum
- Shared-memory communication
- Real-time PyQt5 graph
- PyQtGraph visualization


## Shared Memory
The C process writes spectrum data and the Python process reads the same memory region:
```text
C Producer -> Shared Memory -> Python Consumer
```

## Error Handling
Handle missing shared memory, attachment failures, invalid data, conversion errors, and GUI update errors.

## Result
A single PyQt5 window continuously displays the 1024-channel spectrum without opening new graph windows.


