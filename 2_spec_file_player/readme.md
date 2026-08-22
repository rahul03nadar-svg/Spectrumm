# 2 – Spectrum File Player

## Objective
Read a spectrum from a TXT or CSV file and simulate real-time acquisition by sending one spectrum through shared memory every second. A second PyQt5 application displays the live spectrum.

## Architecture
```text
TXT/CSV Spectrum -> Spectrum Player -> Shared Memory -> PyQt5 Viewer -> Live Spectrum
```

## Technologies
- C / GCC or the implemented player language
- Linux shared memory
- Python 3
- PyQt5
- PyQtGraph
- NumPy


## Playback
Bonus controls:
- Play: continue playback
- Pause: temporarily stop playback
- Restart: return to the first spectrum

## Error Handling
Handle missing files, empty files, invalid numerical values, incorrect spectrum format, shared-memory errors, and invalid channel counts.

## Result
The PyQt5 viewer displays a spectrum and receives approximately one new spectrum every second.
