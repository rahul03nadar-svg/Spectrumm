# 3 – Peak Detection

## Objective
Develop a PyQt5 application that reads a spectrum, automatically detects peaks, displays peak positions on the graph, and reports the channel number and peak height. An adjustable threshold can be used to ignore noise.

## Architecture
```text
Spectrum -> Python Application -> Peak Detection -> Peak Position/Height -> PyQt5 Graph
```

## Technologies
- Python 3
- PyQt5
- PyQtGraph
- NumPy
- SciPy
- scipy.signal.find_peaks (for peak detection)


## Threshold
A threshold can remove small noise peaks. Increasing the threshold generally produces fewer detected peaks.


## Error Handling
Handle missing files, empty spectra, invalid data, invalid thresholds, no detected peaks, and incorrect input formats.

## Result
The GUI displays the spectrum with detected peaks marked and reports their channel positions and heights.
