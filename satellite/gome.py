import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import h5py
import glob
from tqdm import tqdm
import verde as vd
import pyproj
from mpl_toolkits.basemap import Basemap


'''
script to read GOME2 Trace Gas column data
Satellite Platform (MetOpA, MetOpAB, MetOpC)
species: 'O3', 'NO2', 'NO2Tropo', 'HCHO', 'H2O', 'SO2', 'BrO'
'''


class GOMEColumn():
    '''
    python class to read GOME data and perform gridding and resample.
    
    
    
    Example:
    ```python
    gcol = GOMEColumn(filename) 
    # filename is the name of GOME2 data file to be read.
    # read raw data (both trace gas and geolocation)
    data = gcol.read(fields=['O3', 'NO2'])
    
    # Perform gridding of data using latlon projection specifying the region boundary and resolution
    new = gcol.grid_data(field, region=(-180, 179.8, -89.75, 89.75), spacing=0.1, positive=True)
    ```
    
    Here spacing stands for the resoultion of grids.
    region specifies the latitude and longitude ranges.
    
    '''
    def __init__(self, filename):
        self.filename = filename
        
    def read(self, fields=['O3', 'NO2', 'NO2Tropo', 'HCHO', 'H2O', 'SO2', 'BrO']):            
        data = pd.DataFrame([])
        with h5py.File(self.filename, 'r') as f:
            geo = f['GEOLOCATION']
            data['lat'] = geo['LatitudeCentre'][()]
            data['lon'] = geo['LongitudeCentre'][()]
            data['lsa'] = geo['LineOfSightZenithAngleCentre'][()]
            data['raz'] = geo['RelativeAzimuthCentre'][()]
            data['sza'] = geo['SolarZenithAngleCentre'][()]
            for field in fields:
                data[field] = f['TOTAL_COLUMNS'][field][()]  
        data = data.to_xarray()
        return data
    
    def grid_data(self, field, attrs={'long_name': ''}, region=(-180, 179.8, -89.75, 89.75), spacing=0.1, positive=True): 
        data = self.read(fields=[field])
        lon = data['lon'].values
        lat = data['lat'].values
        mol = data[field].values
        if positive:
            mol[mol<=0] = np.nan
        
        coordinates = (lon, lat)
        if region:
            region = region
        else:
            region = vd.get_region(coordinates)

        projection = pyproj.Proj(proj="latlon")
        proj_coordinates = projection(*coordinates)

        grd = vd.ScipyGridder(method="linear").fit(proj_coordinates, mol)
        grid = grd.grid(region=region, spacing=spacing, projection=projection, dims=["lat", "lon"], data_names=[field])
        new = vd.distance_mask(coordinates, maxdist= 6 * spacing, grid=grid, projection=projection)[field]
        new.attrs = attrs
        return new

class GOME():
    '''
    python class to read GOME data and perform gridding and resample.
    
    
    Example:
    ```python
    gome = GOME(files, field, resolution) 
    # files is the names of GOME2 data files to be read. 
    # field represents trace gas fieldname (option=['O3', 'NO2', 'NO2Tropo', 'HCHO', 'H2O', 'SO2', 'BrO'])
    
    gome = gome.resample(freq='D') 
    # gridding and resampling of data with frequecy given as freq.
    
    fig, ax, cb, m = gome.plot() 
    # plotting the resampled data using cylindrical projection with Basemap. 
    ```
    
    '''

    def __init__(self, files, field='O3', spacing=0.1):
        self.files = files
        self.field = field
        self.resolution = spacing
    
    def resample(self, freq='D'):
        new = []
        time = []
        for filename in tqdm(self.files):
            gome = GOMEColumn(filename)
            data = gome.grid_data(self.field, spacing=self.resolution)  
            new.append(data)
            time.append(pd.to_datetime(filename.split('_')[3]))
        new = xr.concat(new, dim='time')
        new['time'] = time
        self.data = new.resample(time=freq).mean(dim=['time'])
        return self
    
    def plot(self, scale=1, cax=[0.85, 0.2, 0.02, 0.6], figsize=(14, 7)):
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        cb = fig.add_axes(cax)
        m = Basemap(projection='cyl', ax=ax)
        (scale*self.data).plot(ax=ax, cbar_ax=cb)
        m.drawmapboundary(color='k')
        m.drawcoastlines(color='k')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        return fig, ax, cb, m
