import rasterio
import rasterio.features
import shapely.affinity
import shapely.geometry
import shapely.ops
import yaml
import uuid
import sys
from os import path
from datetime import datetime
cyclone_name = {
    'Ingrid_Landfall2':'IngridLF2',
    'Laurence':'Laurence', 
    'Lam':'Lam',
    'Ita':  'Ita',
    'Monica_Landfall1':'MonicaLF1',
    'Nathan_Landfall2':'NathanLF2',
    'Marcia': 'Marcia', 
    'Nathan_Landfall1':'NathanLF1',
    'Ingrid_Landfall1': 'IngridLF1',   
    'George':'George',
    'Larry':'Larry',
    'Yas':'Yasi',  
    'Ingrid_Landfall3':'IngridLF3',
    'Monica_Landfall2':'MonicaLF2'
} 

cyclone_time = {
        'IngridLF1':  '2005-01-01T00:00:00',
        'IngridLF2':   '2005-01-01T00:00:00', 
        'IngridLF3':   '2005-01-01T00:00:00',
        'Larry':  '2006-01-01T00:00:00',
        'MonicaLF1':   '2006-01-01T00:00:00',    
        'MonicaLF2':   '2006-01-01T00:00:00',
        'George':  '2007-01-01T00:00:00',
        'Laurence':    '2009-01-01T00:00:00',
        'Yasi':    '2011-01-01T00:00:00',
        'Ita': '2014-01-01T00:00:00',
        'Lam': '2015-01-01T00:00:00',
        'Marcia':  '2015-01-01T00:00:00',
        'NathanLF1':   '2015-01-01T00:00:00',
        'NathanLF2':  '2015-01-01T00:00:00',
        'Debbie': '2017-01-01T00:00:00'
        }

def _to_lists(x):
    """
    Returns lists of lists when given tuples of tuples
    """
    if isinstance(x, tuple):
        return [_to_lists(el) for el in x]
    return x

def valid_region(fname):
    """
    Return valid data region for input images based on mask value and input image path
    """
    with rasterio.open(fname, 'r') as dataset:
        transform = dataset.transform
        crs = dataset.crs
        bounds = dataset.bounds
        img = dataset.read(1)
        mask = img > 0
    shapes = rasterio.features.shapes(mask.astype('uint8'), mask=mask)
    shape = shapely.ops.unary_union([shapely.geometry.shape(shape) for shape, val in shapes if val == 1])
    # convex hull
    geom = shape.convex_hull
    # buffer by 1 pixel
    geom = geom.buffer(1, join_style=3, cap_style=3)
    # simplify with 1 pixel radius
    geom = geom.simplify(1)
    # intersect with image bounding box
    geom = geom.intersection(shapely.geometry.box(0, 0, mask.shape[1], mask.shape[0]))
    # transform from pixel space into CRS space
    geom = shapely.affinity.affine_transform(geom, (transform.a, transform.b, transform.d,
                                                    transform.e, transform.xoff, transform.yoff))
    return bounds, crs, geom 

def get_coords(bounds):
    """
    Returns transformed coordinates in latitude and longitude from input
    reference points and spatial reference
    """
    tlat = bounds.top
    blat = bounds. bottom
    llon = bounds.left
    rlon = bounds.right
    return {'ll': {'lat': blat, 'lon': llon}, 
            'lr': {'lat': blat, 'lon': rlon},
            'ul': {'lat': tlat, 'lon': llon},
            'ur': {'lat': tlat, 'lon': rlon}}

def get_ref_points(bounds):
    tlat = bounds.top
    blat = bounds. bottom
    llon = bounds.left
    rlon = bounds.right
    return {'ll': {'x': blat, 'y': llon}, 
            'lr': {'x': blat, 'y': rlon},
            'ul': {'x': tlat, 'y': llon},
            'ur': {'x': tlat, 'y': rlon}}



def prepare_dataset(wfile):
    """
    Returns yaml content based on content found at input file path
    """
    # Looks like sometimes the stop time is before the start time....maybe just set them to be the same
    ct_time = datetime.now()
    base_name = path.basename(wfile.strip('.tif'))
    center_time = datetime.strptime(cyclone_time[cyclone_name[base_name]], "%Y-%m-%dT%H:%M:%S")
    start_time = datetime.strptime(cyclone_time[cyclone_name[base_name]], "%Y-%m-%dT%H:%M:%S")
    stop_time = datetime.strptime(cyclone_time[cyclone_name[base_name]], "%Y-%m-%dT%H:%M:%S")
    bounds, crs, geom = valid_region(wfile)
    documents = []
    img_dict = {}
    img_dict['wind_speed'] = {'path': wfile, 'layer': 1}
    documents.append({
        'id': str(uuid.uuid5(uuid.NAMESPACE_URL, wfile)),
        'product_type': 'windspeed',
        'creation_dt': ct_time,
        'platform': {'code': 'IDN'},
        'instrument': {'name': 'IDN'},
        'format': {'name': 'GeoTIFF'},
        'extent': {
            'from_dt': start_time,
            'to_dt': stop_time,
            'center_dt': center_time,
            'coord': get_coords(bounds),
        },
        'grid_spatial': {
            'projection': {
                'geo_ref_points': get_ref_points(bounds),
                'spatial_reference': crs.wkt,
                'valid_data': {
                    'coordinates': _to_lists(
                        shapely.geometry.mapping(
                            shapely.ops.unary_union([
                                geom
                            ])
                        )['coordinates']),
                    'type': "Polygon"}
            }
        },
        'image': {
            'bands': img_dict
        },

        'lineage': {'source_datasets': {}},
    })
    return documents

def main(wfile):
    doc = prepare_dataset(wfile)
    yaml_path = 'windspeed/' + path.basename(wfile.strip('.tif') + '.yaml')
    with open(yaml_path, 'w') as stream:
        yaml.dump_all(doc, stream, default_flow_style=False)

if __name__ == '__main__':

    nargv = len(sys.argv)
    if nargv!=2:
        print("Usage: whatever.py filename")
        exit()
    else:
        args = sys.argv[1:]
    main(*args)

