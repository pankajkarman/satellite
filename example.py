from satellite import MLSProfile
from satellite import OMPSProfile
import glob

filename1 = glob.glob('/media/pankaj/ext2/data/profile/clo/*.he5')[0]
biasfile = '/home/pankaj/phd/code/satellite/satellite/MLS-Aura_ClO-BiasCorrection_v04.txt'

mls = MLSProfile(filename1)
concentration, precision = mls.correct(biasfile=biasfile)

filename2 = glob.glob('/media/pankaj/ext2/data/profile/omps/*.h5')[0]
omps = OMPSProfile(filename2)
UVozone, UVozonePrecision, VisibleOzone, VisibleOzonePrecision = omps.correct(vmr=True)
