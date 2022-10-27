
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
from datacube.utils.cog import write_cog

def read_data_from_netcdf(fname):
    dataset_array = xr.open_dataset(fname)
    data = dataset_array.canopy_cover_class
    #data.values[np.isnan(dataset_array.extent.values)]  = 0
    return data

def categorize_damage(bc_canopy, ac_canopy):
    nodata = int(bc_canopy.attrs.get('nodatavals')[0])
    reduction = xr.DataArray(data=np.zeros(bc_canopy.shape, dtype='int16'), dims=['band', 'y', 'x'], coords={'band': [1], 'y': bc_canopy.coords['y'],
        'x': bc_canopy.coords['x']})
    reduction.attrs = bc_canopy.attrs
    reduction.attrs.pop('nodatavals')
    reduction.attrs['nodata'] = 0
    reduction.values[(bc_canopy.values == 0) | (ac_canopy.values == 0)] = 101
    reduction.values[bc_canopy.values == ac_canopy.values] = 101
    reduction.values[(bc_canopy.values >= 2) & (ac_canopy.values == nodata)] = 105
    reduction.values[(bc_canopy.values == 1) & (ac_canopy.values == nodata)] = 104
    reduction.values[(bc_canopy.values == 3) & (ac_canopy.values == 1)] = 103
    reduction.values[(bc_canopy.values == 3) & (ac_canopy.values == 2)] = 102
    reduction.values[(bc_canopy.values == 2) & (ac_canopy.values == 1)] = 102
    reduction.values[(bc_canopy.values == nodata) & (ac_canopy.values >= 1)] = 201
    reduction.values[(bc_canopy.values == 1) & (ac_canopy.values == 2)] = 202
    reduction.values[(bc_canopy.values == 2) & (ac_canopy.values == 3)] = 202
    reduction.values[(bc_canopy.values == 1) & (ac_canopy.values == 3)] = 203
    reduction.values[(bc_canopy.values == nodata) & (ac_canopy.values == nodata)] = 0
    return reduction


def main(x1, y1, year, name):
    mangrove_folder = '/g/data/fk4/datacube/002/MANGROVE_COVER/MANGROVES_2_0_2/MANGROVE_COVER/x_%s/y_%s/'%(x1, y1)
    start = int(year)
    end = int(year) + 1
    bc_file = '%s/MANGROVE_COVER_3577_'%start  + '_'.join([str(x1), str(y1), str(start)]) + '0101_canopy_cover_class.tif'
    bc_file = path.join(mangrove_folder, bc_file)
    print("file before cyclone", bc_file)

    bc_canopy = xr.open_rasterio(bc_file, parse_coordinates=True)
    while True:
        ac_file = '%s/MANGROVE_COVER_3577_'%end  + '_'.join([str(x1), str(y1), str(end)]) + '0101_canopy_cover_class.tif'
        ac_file = path.join(mangrove_folder, ac_file)
        print("file after cyclone", ac_file)
        if path.exists(ac_file) == False:
            return

        ac_canopy = xr.open_rasterio(ac_file, parse_coordinates=True)

        result = categorize_damage(bc_canopy, ac_canopy)
        dir_name = 'gulf_carpentaria/'
        if os.path.exists(dir_name) == False:
            os.mkdir(dir_name)
        fout = '_'.join([name, str(x1), str(y1), str(start), str(end)]) + '.tif'
        write_cog(result, path.join(dir_name, fout))
        end += 1

if __name__ == '__main__':

    nargv = len(sys.argv)
    if nargv!=5:
        print("Usage: whatever.py x1 y1 year cyclon-name")
        exit()

    args = sys.argv[1:]
    main(*args)
