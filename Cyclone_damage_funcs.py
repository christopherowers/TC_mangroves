import datacube
from datacube.model import Measurement
import numpy as np
import xarray as xr
from os import path
from datacube.drivers.netcdf import write_dataset_to_netcdf
from datacube.utils.geometry import CRS
import pandas as pd
import os
from  datacube import Datacube
from datacube.utils import geometry
import pickle
import sys
import rioxarray
dc = datacube.Datacube(app="cyclone mangroves")


windspeed_category = {'C1': [0., 125*1000/60**2],
                        'C2':[125*1000/60**2, 165*1000/60**2],
                        'C3': [165*1000/60**2, 225*1000/60**2], 
                        'C4': [225*1000/60**2, 280*1000/60**2],
                        'C5': [280*1000/60**2, 9999.]}


def categorize_damage(bc_canopy, ac_canopy):
    '''
    On the mangrove classes. Difference before cyclone and after cyclone.
    '''
    reduction = bc_canopy - ac_canopy
    return reduction



def damage_level_by_geo(dir_name, cyclone_name, cyclone_data, bc_datasets, ac_datasets, loading_box, dump=True):
    '''
    dir_name: directory output for results
    cyclone_name: string name
    cyclone_data: xr.dataset of the cyclone windfield
    bc_datasets: mangrove canopy cover datasets before the cyclone (using time from cyclone dataset)
    ac_datasets: mangrove canopy cover datasets after the cyclone (using time from cyclone dataset)
    loading_box: bounding box (30m res) of the cyclone extent
    dump: writing out cyclone damage results
    '''
    
    # measurements for mangrove canopy cover
    measurement = [Measurement(name='canopy_cover_class', dtype='int16', nodata=-1, units='1')]
    # load mangrove canopy cover from find.datasets that are before the cyclone
    bc_canopy = dc.load_data(bc_datasets, geobox = loading_box, measurements=measurement)
    
    immediate = 0
    
    # make sure dir exists, otherwise make, for result outputs
    if dump:
        dir_name += '/' + cyclone_name
        if path.exists(dir_name) == False:
            os.mkdir(dir_name)
    
    # for time in after cyclone mangrove canopy cover datasets
    for t in ac_datasets.time.data:
        # load the data for the time step (they are not loaded yet, just find.datasets has been used)
        ac_canopy = dc.load_data(ac_datasets.sel(time=[t]), geobox = loading_box, measurements=measurement)
        # use the categorize_damage function above to work out damage (not sure how this works with multiple times for bc_datasets)
        damage_label = categorize_damage(bc_canopy.canopy_cover_class.data, ac_canopy.canopy_cover_class.data)
        
        ### relabel the categorize_damage data
        # -1 no mangroves
        # 0 is not observed/missing data
        # Immediate damage is 0-4 for before minus after mangrove class
        damage_label[np.logical_and(bc_canopy.canopy_cover_class.data == -1, ac_canopy.canopy_cover_class.data == -1)] = -1 
        damage_label[np.logical_or(bc_canopy.canopy_cover_class.data == 0, ac_canopy.canopy_cover_class.data == 0)] = -1 
        # Open forest to no mangroves == cat 4 damage
        damage_label[np.logical_and(bc_canopy.canopy_cover_class.data == 2, ac_canopy.canopy_cover_class.data == -1)] = 4 # reduce from 2 
        # Closed forest to no mangroves == cat 4 damage
        damage_label[np.logical_and(bc_canopy.canopy_cover_class.data == 3, ac_canopy.canopy_cover_class.data == -1)] = 4 # reduce from 3
        # Open woodland to no mangroves == cat 3 damage
        damage_label[np.logical_and(bc_canopy.canopy_cover_class.data == 1, ac_canopy.canopy_cover_class.data == -1)] = 3 # reduce from 1 
        damage_label[damage_label < 0] = -1
        
        # writing out category immediate damage after cyclone data to xarray to export as netcdf
        ac_canopy.time.attrs['units'] = "seconds since 1970-01-01 00:00:00"
        result  = xr.Dataset({"damage_level":(['time', 'y', 'x'], damage_label.astype('int16'))},
                    coords={'time':ac_canopy.time, 'y': ac_canopy.y, 'x':ac_canopy.x},
                    attrs={'crs': CRS('EPSG:3577'), 'nodata': -1})
        fout = '_'.join([cyclone_name, "%s" % int(ac_canopy.x.data.min()/10000), 
            "%s" % int(ac_canopy.y.data.min()/10000), 
            "%.10s" % str(bc_canopy.time[0].data), 
            "%.10s" % str(ac_canopy.time[0].data)]) + '.nc'
        
        if dump:
            # writing out just the damage categories
            # immediate damage; before minus after
            write_dataset_to_netcdf(result, path.join(dir_name, fout))
        
        # now add in the wind speed and calculate immediate impact of the cyclone by area
        # 5 wind speed categories so a loop with five iterations
        if immediate == 0:
            wind_cat = pd.DataFrame(index=list(windspeed_category.keys()), columns=np.arange(0,5))
            for key, value in windspeed_category.items():
                wind_damage = result.damage_level[0].where(np.logical_and(cyclone_data.wind_speed[0] >= value[0] 
                                            ,cyclone_data.wind_speed[0] < value[1]))
                for i in range(0, 5): # damage levels
                    wind_cat[i][key] = wind_damage.where(wind_damage == i).count().data * 0.030**2
            print(wind_cat)
            all_damage_level = result.damage_level
        else:
            all_damage_level = xr.concat([all_damage_level, result.damage_level], dim='time')
        immediate += 1

    # categorise long term damage from the cyclone
    # categories 1-5 for long term damage using time
    results = np.zeros(all_damage_level.shape[1:], dtype='int16')
    tmp = all_damage_level.where(np.logical_and(all_damage_level<=2, all_damage_level > 0)).count(dim='time')
    results[tmp.values > 0] = 1 # at least once
    results[tmp.values==all_damage_level.time.shape[0]] = 2 # for whole time period after cyclone

    tmp = all_damage_level.where(np.logical_and(all_damage_level<=4, all_damage_level > 2)).count(dim='time')
    results[tmp.values > 0] = 3 # at least once
    results[tmp.values==all_damage_level.time.shape[0]] = 4 # for whole time after cyclone

    tmp = all_damage_level.where(all_damage_level==4).count(dim='time') # always a level 4 - never recovered
    results[tmp.values==all_damage_level.time.shape[0]] = 5
    results[all_damage_level.values[0]==-1] = -1

    
    # writing out category long term damage after cyclone data to xarray to export as netcdf
    all_damage_level.time.attrs['units'] = "seconds since 1970-01-01 00:00:00"
    results = results.reshape((1, ) + results.shape)
    results = xr.Dataset({"damage_level":(['time', 'y', 'x'], results.astype('int16'))},
                coords={'time':all_damage_level.time[-1:], 'y': all_damage_level.y, 'x': all_damage_level.x},
                attrs={'crs': CRS('EPSG:3577'), 'nodata': -1})
    fout = '_'.join([cyclone_name, "%s" % int(all_damage_level.x.data.min()/10000), 
        "%s" % int(all_damage_level.y.data.min()/10000)]) + '_all.nc'
    
    if dump:
        write_dataset_to_netcdf(results, path.join(dir_name, fout))
    all_wind_cat = pd.DataFrame(index=list(windspeed_category.keys()), columns=np.arange(1,6))
    
    for key, value in windspeed_category.items():
        wind_damage = results.damage_level[0].where(np.logical_and(cyclone_data.wind_speed[0] >= value[0],
                                cyclone_data.wind_speed[0] < value[1]))
        for i in range(0, 5):
            all_wind_cat[i+1][key] = wind_damage.where(wind_damage == (i+1)).count().data * 0.030**2
    print(all_wind_cat)

    return wind_cat, all_wind_cat