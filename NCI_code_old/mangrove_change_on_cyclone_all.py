
import datacube
import sys
import rasterio
import numpy as np
import time
import os
import subprocess
from datacube.drivers.netcdf import netcdf_writer
from datacube.drivers.netcdf import create_netcdf_storage_unit, write_dataset_to_netcdf
import xarray as xr
from os import path
from datacube.model import Measurement  
from datacube.model import DatasetType as Product
from datacube.model.utils import make_dataset, xr_apply, datasets_to_doc
from pathlib import Path
from datacube.api.query import query_group_by, query_geopolygon
from datacube.utils.geometry import CRS
import yaml
from yaml import CSafeLoader as Loader, CSafeDumper as Dumper

def read_data_from_netcdf(fname):
    dataset_array = xr.open_dataset(fname)
    return dataset_array.damage_level

def count_damage(damage_level, axis,  label=0):
    print("count", label)
    print("axis", axis)
    return np.unique(damage_level, axis=axis, return_counts=True)[1]

def main(x1, y1, year, name):
    start = int(year)
    end = int(year) + 1
    dir_name = 'cyclone_damage_results_v2/' + name 

    fin = '_'.join([name, str(x1), str(y1), str(start), str(end)]) + '.nc'
    fin = path.join(dir_name, fin)
    if path.exists(fin) == False:
        return
    
    damage_level = read_data_from_netcdf(fin)
    results = np.zeros(damage_level.shape[1:], dtype='int16')

    while True:
        end += 1
        fin = '_'.join([name, str(x1), str(y1), str(start), str(end)]) + '.nc'
        fin = path.join(dir_name, fin)
        if path.exists(fin) == False:
            break

        damage_level = xr.concat([damage_level, read_data_from_netcdf(fin)], dim='time')

    tmp = damage_level.where(np.logical_and(damage_level<=2, damage_level > 0)).count(dim='time')
    results[tmp.values > 0] = 1
    results[tmp.values==damage_level.time.shape[0]] = 2

    tmp = damage_level.where(np.logical_and(damage_level<=4, damage_level > 2)).count(dim='time')
    results[tmp.values > 0] = 3
    results[tmp.values==damage_level.time.shape[0]] = 4

    tmp = damage_level.where(damage_level==4).count(dim='time')
    results[tmp.values==damage_level.time.shape[0]] = 5
    results[damage_level.values[0]==-1] = -1

    damage_level.time.attrs['units'] = "seconds since 1970-01-01 00:00:00"
    results = results.reshape((1, ) + results.shape)
    results = xr.Dataset({"damage_level":(['time', 'y', 'x'], results)}, 
            coords={'time':damage_level.time[-1:], 'y': damage_level.y, 'x': damage_level.x},
                attrs={'crs': CRS('EPSG:3577')})
    print(results)

    fout = '_'.join([name, str(x1), str(y1), 'all']) + '.nc'
    write_dataset_to_netcdf(results, path.join(dir_name, fout))

if __name__ == '__main__':

    nargv = len(sys.argv)
    if nargv!=5:
        print("Usage: whatever.py x1 y1 year name")
        exit()

    args = sys.argv[1:]
    main(*args)
