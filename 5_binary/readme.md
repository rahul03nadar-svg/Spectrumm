# 5 – Binary Data Logger

## Objective
Receive spectrum data from shared memory and store every spectrum in a binary file. Develop another application that reads the recorded data and replays it in a PyQt5 GUI.

## Architecture
```text
Spectrum Generator -> Shared Memory -> Binary Logger -> spectrum.bin -> Replay Viewer -> PyQt5 GUI
```
## Technologies
- C
- Python 3
- Linux shared memory
- Binary files
- PyQt5
- PyQtGraph
- NumPy

## Binary Storage
Binary storage keeps numerical data in binary representation rather than human-readable text:
```text
Spectrum -> Binary Encoding -> spectrum.bin
spectrum.bin -> Binary Decoding -> Spectrum -> GUI
```

## Replay Controls
Possible controls:
- Play
- Pause
- Restart
- Stop

## Error Handling
Handle missing or empty binary files, corrupt/incomplete frames, invalid frame sizes, and shared-memory failures.

## Result
The replay GUI displays recorded spectra one after another at a controlled playback rate.
