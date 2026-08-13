# 6 – Multi-Process Communication

## Objective
Create three separate applications:
1. Spectrum Generator – C
2. Data Processor – Python
3. Spectrum Viewer – Python/PyQt5

The generator writes raw spectrum data into shared memory. The processor reads it, applies a moving average filter, and writes processed data into another shared-memory block. The viewer reads the processed data and displays the live spectrum.

## Architecture
```text
C Generator
    |
    v
Raw Shared Memory
    |
    v
Python Data Processor
    |
    | Moving Average
    v
Processed Shared Memory
    |
    v
Python PyQt5 Viewer
    |
    v
Processed Live Spectrum
```

## Technologies
- C / GCC
- Linux shared memory
- Python 3
- PyQt5
- PyQtGraph
- NumPy

## Moving Average
A moving average uses neighboring samples to smooth the signal.

For a window of 3:
```text
10 20 30 40 50
```

The resulting averages include:
```text
(10+20+30)/3 = 20
(20+30+40)/3 = 30
(30+40+50)/3 = 40
```

## Two Shared-Memory Blocks used because
The first block contains raw data and the second contains processed data:
```text
Shared Memory 1 -> Raw Spectrum
Shared Memory 2 -> Smoothed Spectrum
```

## Error Handling
Handle generator-not-running conditions, unavailable shared memory, invalid spectrum sizes, invalid data, processing errors, and viewer connection failures.

## Result
The viewer displays a smoothed spectrum with reduced rapid fluctuations compared with the raw spectrum.


