# 4 – Live Data Acquisition Simulator

## Objective
Create two applications. The C Producer generates random detector counts every 100 ms and writes them into shared memory. The Python PyQt5 Consumer reads the values and displays the current count, average count, maximum count, and a live graph.

## Architecture
```text
C Producer -> Shared Memory -> Python PyQt5 Consumer
                                  |
                                  +-> Current Count
                                  +-> Average Count
                                  +-> Maximum Count
                                  +-> Live Graph
```

## Technologies
- C
- GCC
- Linux shared memory
- Python 3
- PyQt5
- PyQtGraph
- NumPy

## Statistics
Current Count is the newest received value.
Average Count is calculated from received values.
Maximum Count is the highest value received during the session.

## Start/Stop
If implemented, Start and Stop controls can control whether acquisition is active.

## Error Handling
Handle producer-not-running conditions, shared-memory failures, invalid counts, and GUI update errors.

## Result
The GUI continuously displays current, average, and maximum counts together with a live graph.

