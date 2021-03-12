import h5py
import numpy as np
import pandas as pd
from scipy import interpolate

class MLSProfile():
    '''
    script to read MLS profiles
    
    **MLS data version:** v4.2
    
    **species:** GPH, Temperature, Ozone, Water vapour, N<sub>2</sub>O, CLO, HNO<sub>3</sub>
    
   

    Example:
    ```python
    mls = MLSProfile(filename) 
    # filename is the name of mls data file to be read.
    
    # read geolocation fields    
    latitude, Longitude, levels, LineOfSightAngle, local solar time, oga, sza, tim, chn = mls.read(dtype='geolocation')
    ```
    '''
    def __init__(self, filename):
        self.filename  = filename
        self.fieldname = filename.split('-')[2].split('_')[0]

    def read(self, dtype='geolocation'):
        '''
        function to read profile and other data.
        Here, dtype specifies the data type to be returned.
        options include: geolocation and data.
        '''
        field = self.fieldname
        with h5py.File(self.filename, 'r') as f:
            data = f['HDFEOS']['SWATHS'][field]
            if dtype=='geolocation':
                lat = data['Geolocation Fields']['Latitude'][()]
                lon = data['Geolocation Fields']['Longitude'][()]
                lev = data['Geolocation Fields']['Pressure'][()]
                lsa = data['Geolocation Fields']['LineOfSightAngle'][()]
                lst = data['Geolocation Fields']['LocalSolarTime'][()]
                oga = data['Geolocation Fields']['OrbitGeodeticAngle'][()]
                sza = data['Geolocation Fields']['SolarZenithAngle'][()]
                tim = data['Geolocation Fields']['Time'][()]
                chn = data['Geolocation Fields']['ChunkNumber'][()]
                return lat, lon, lev, lsa, lst, oga, sza, tim, chn

            if dtype=='data':
                con = data['Data Fields']['Convergence'][()]
                prc = data['Data Fields']['L2gpPrecision'][()]
                mol = data['Data Fields']['L2gpValue'][()]
                qua = data['Data Fields']['Quality'][()]
                sta = data['Data Fields']['Status'][()]
                nlev = data['nLevels'][()]
                nlev = len(nlev)
                ntim = data['nTimes'][()]
                ntim = len(ntim)
                return field, con, prc, mol, qua, sta, nlev, ntim

    def correct(self, biasfile='MLS-Aura_ClO-BiasCorrection_v04.txt'):
        '''
        function to correct atmospheric composition data. Consult MLS data quality and description document for details.
        Here, biasfile is used for correcting ClO data only. for all other species, it can be set to None.

        example:
        ```python
        mol, prc = mls.correct()
        ```
        '''
        lat, lon, pre, lsa, lst, oga, sza, tim, chn = self.read(dtype='geolocation')
        field, con, prc, mol, qua, sta, nlev, ntim = self.read(dtype='data')
        mol[prc<=0] = np.nan

        if field in ['GPH', 'Temperature']:
            criteria1 = (con<1.03) & (qua>0.2) & (sta%2==0)
            criteria2 = (pre>0.001) & (pre<261)
            criteria3 = (pre>=100)
            criteria4 = (qua>0.9)
            for var in [mol, prc]:
                var[~criteria1, :] = np.nan
                var[:, ~criteria2] = np.nan
                var[:, criteria3][~criteria4, :]  = np.nan

        if field == 'O3':
            do = (pre>260) & (pre<262)
            eo = (pre<0.018)
            ll = (pre>314) & (pre<318)
            hl = (pre>=0.0018) & (pre<0.0025)

            criteria1 = (con<1.03) & (qua>1.0) & (sta%2==0)
            criteria2 = (pre>0.02) & (pre<261)
            for var in [mol, prc]:
                var[~criteria1, :] = np.nan
                var[:, ~criteria2] = np.nan
                var[:, ll | eo] = np.nan

        if field == 'H2O':
            criteria1 = (con<2.0) & (qua>1.45) & (sta%2==0) & (sta!=16) & (sta!=32)
            criteria2 = (pre>0.002) & (pre<317)
            for var in [mol, prc]:
                var[~criteria1, :] = np.nan
                var[:, ~criteria2] = np.nan

        if field == 'N2O':
            criteria1 = (con<2.0) & (qua>1.0) & (sta%2==0) & (sta!=16) & (sta!=32)
            criteria2 = (pre>0.45) & (pre<69)
            for var in [mol, prc]:
                var[~criteria1, :] = np.nan
                var[:, ~criteria2] = np.nan

        if field == 'ClO':
            bs = pd.read_csv(biasfile, skiprows=13, sep='\s+', dtype='float', na_values=-999.99)
            bs.columns = ['146.78', '100.00','68.13']
            bs = bs.ffill().bfill()

            bias1 = interpolate.interp1d(bs.index, bs['146.78'])
            bias2 = interpolate.interp1d(bs.index, bs['100.00'])
            bias3 = interpolate.interp1d(bs.index, bs['68.13'])

            mol[:, 5] -= bias1(lat)
            mol[:, 6] -= bias2(lat)
            mol[:, 7] -= bias3(lat)
            #mol[mol<0] = np.nan

            criteria1 = (con<1.05) & (qua>1.3) & (sta==0)
            criteria2 = (pre>1.0) & (pre<147)
            #criteria3 = (sza<=89)
            #criteria4 = (10<=lst) & (lst<=16)
            for var in [mol, prc]:
                var[~criteria1, :] = np.nan
                var[:, ~criteria2] = np.nan
                #var[~criteria3, :] = np.nan
                #var[~criteria4, :] = np.nan

        if field == 'HNO3':
            criteria1 = (sta%2==0)
            criteria2 = (pre>0.001) & (pre<261)
            criteria3 = (pre>=22)
            criteria4 = (qua>0.8)  & (con<1.03)
            for var in [mol, prc]:
                var[~criteria1, :] = np.nan
                var[:, ~criteria2] = np.nan
                var[:, criteria3][~criteria4, :]  = np.nan
        return mol, prc
