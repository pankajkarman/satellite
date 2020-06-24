
Python scripts to read and correct of satellite atmospheric composition profile data.

## Implemented satellites inlcude:
- [Aura-MLS](https://mls.jpl.nasa.gov/)
- [Suomi- NPP OMPS](https://www.star.nesdis.noaa.gov/icvs/status_NPP_OMPS_LP.php)

# Usage

```python
from satellite import MLSProfile
from satellite import OMPSProfile
```

## for MLS Profiles

```python
filename = '/media/pankaj/ext2/data/profile/clo/MLS-Aura_L2GP-ClO_v04-20-c01_2010d335.he5'
biasfile = '/home/pankaj/phd/code/satellite/satellite/MLS-Aura_ClO-BiasCorrection_v04.txt'

mls = MLSProfile(filename)
concentration, precision = mls.correct(biasfile=biasfile)
```

## for OMPS Ozone profiles

```python
filename = '/media/pankaj/ext2/data/profile/omps/OMPS-NPP_LP-L2-O3-DAILY_v2.5_2019m1201_2019m1202t142927.h5'
omps = OMPSProfile(filename2)
UVozone, UVozonePrecision, VisibleOzone, VisibleOzonePrecision = omps.correct(vmr=True)
```