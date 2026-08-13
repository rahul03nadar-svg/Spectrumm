# 7 – Gaussian Peak Fitting

## Objective
Develop a PyQt5 application that fits a Gaussian function to a selected peak in a spectrum.

The application should load a TXT/CSV spectrum, plot it, allow a fitting region to be selected, fit the region, and display the original spectrum, fitted Gaussian, amplitude, centroid, standard deviation, and FWHM.

## Gaussian Function
```python
def gaussian(x, amplitude, mean, stddev):
    return amplitude * np.exp(-(x - mean)**2 / (2 * stddev**2))
```
Where:
- A = peak amplitude
- μ = peak centroid/mean
- σ = standard deviation

## FWHM
FWHM = 2.355 * sigma
```

## Architecture
```text
Spectrum File
     |
     v
PyQt5 Application
     |
     v
Select Fitting Region
     |
     v
Gaussian Fit
     |
     -> Amplitude
     -> Centroid
     -> Standard Deviation
     -> FWHM
     |
     v
Original + Fitted Curve
```

## Technologies
- Python 3
- PyQt5
- PyQtGraph
- NumPy
- SciPy


## Selecting a Peak
The user selects a region around the desired peak. Only that region is used for fitting.

## Fitted Parameters
Example:
```text
Amplitude       = 950.42
Centroid        = 512.36
Standard Dev.   = 12.74
FWHM            = 30.00
```

## Fitted Curve
The graph should display both the measured spectrum and the Gaussian curve fitted to the selected region.


## Goodness of Fit
The application can calculate R². A value closer to 1 generally indicates a better fit for the selected region.

## Multiple Peaks
Bonus functionality can fit multiple peaks. Each peak can have its own amplitude, centroid, standard deviation, and FWHM.

## Error Handling
Handle missing files, empty spectra, invalid data, invalid fitting regions, too few points, failed fitting, invalid values, and file-save errors.

## Result
The GUI displays the original spectrum, fitted Gaussian curve, and calculated parameters.


