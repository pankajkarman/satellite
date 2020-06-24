import h5py
import numpy as np

'''
script to read OMPS ozone profiles
OMPS data version: v2.5
'''


class OMPSProfile():
    '''
    omps = OMPSProfile(filename)
    lat, lon, lev, date, time, sza, ssa, tph, cld = omps.read(dtype='aux')
    pre, tem, ouv, puv, ovi, pvi = omps.read(dtype='data')
    slf, adf, quv, qvi, afg, quf, qvf = omps.read(dtype='flags')
    uvres, vires, event, srf = omps.read(dtype='other')
    ouv, puv, ovi, pvi = omps.correct(vmr=True) # if you want vmr in return
    ouv, puv, ovi, pvi = omps.correct(vmr=False) # to return concentration in cm**-3.
    '''
    def __init__(self, filename):
        self.filename = filename

    def read(self, dtype='aux'):
        '''
        function to read profile and other data.
        Here, dtype specifies the data type to be returned.
        options include: aux, data, flags and other.
        '''
        with h5py.File(self.filename, 'r') as f:
            da = f['DataFields']
            gl = f['GeolocationFields']
            an = f['AncillaryData']

            if dtype=='aux':
                '''
                function to return geolocation data fields
                '''
                lat = gl['Latitude'][()]
                lon = gl['Longitude'][()]
                lev = da['Altitude'][()]
                date = gl['Date'][()]
                time = gl['Time'][()]
                sza = gl['SolarZenithAngle'][()]
                ssa = gl['SingleScatterAngle'][()]
                tph = an['TropopauseAltitude'][()]
                cld = da['CloudHeight'][()]
                return lat, lon, lev, date, time, sza, ssa, tph, cld

            if dtype=='data':
                '''
                function to return ozone (Visible and UV-Ozone) and meteorological data (Temperature and Pressure)
                '''
                pre = an['Pressure'][()]
                tem = an['Temperature'][()]
                ouv = da['O3UvValue'][()]
                puv = da['O3UvPrecision'][()]
                ovi = da['O3VisValue'][()]
                pvi = da['O3VisPrecision'][()]
                ouv[ouv==-999] = np.nan
                ovi[ovi==-999] = np.nan
                puv[puv==-999] = np.nan
                pvi[pvi==-999] = np.nan
                return pre, tem, ouv, puv, ovi, pvi

            if dtype=='flags':
                '''
                function to return various flags like ozone quality flags, swath level quality flags. Consult OMPS readme documentation for more information.
                '''
                slf = gl['SwathLevelQualityFlags'][()]
                adf = gl['AscendingDescendingFlag'][()]
                quv = da['O3UvQuality'][()]
                qvi = da['O3VisQuality'][()]
                afg = da['ASI_PMCFlag'][()]
                quf = da['Q_UV'][()]
                qvf = da['Q_VIS'][()]
                quv[quv==-999] = np.nan
                qvi[qvi==-999] = np.nan
                qvi[qvi==2] = np.nan
                return slf, adf, quv, qvi, afg, quf, qvf

            if dtype=='other':
                '''
                function to return data like profile vertical resolution, event Number, surface reflectance.
                '''
                uvres = da['VertRes_O3UV'][()]
                vires = da['VertRes_O3Vis'][()]
                event = da['eventNumber'][()]
                srf = da['sfcReflValue'][()]
                return uvres, vires, event, srf

    def correct(self, vmr=True):
        '''
        function to correct ozone data with respect to various flags. Consult OMPS reamde for details.
        '''
        pre, tem, ouv, puv, ovi, pvi = self.read(dtype='data')
        slf, _, quv, qvi, afg, _, _  = self.read(dtype='flags')
        nna = np.array([a[-1] for a in slf.astype('str')]).astype('float')
        saa = np.array([a[0] for a in slf.astype('str')]).astype('float')
        ovi[qvi==np.nan, :] = np.nan
        ouv[quv==np.nan, :] = np.nan
        pvi[qvi==np.nan, :] = np.nan
        puv[quv==np.nan, :] = np.nan
        for var in [ovi, ouv, pvi, puv]:
            # remove influence of polar mesospheric clouds
            var[afg==1, :] = np.nan
            # remove data influenced by attitude shift due to planned spacecraft maneuver
            var[nna==1, :] = np.nan
            # remove data influenced by South Atlantic Anomaly
            var[saa>=2, :] = np.nan

        if vmr:
            K = 1.38e-19 * tem / pre
            return K*ouv, K*puv, K*ovi, K*pvi
        else:
            return ouv, puv, ovi, pvi
