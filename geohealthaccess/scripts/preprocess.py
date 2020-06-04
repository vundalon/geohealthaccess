"""Preprocess input data."""

import argparse
import os
import shutil

from rasterio.crs import CRS

from geohealthaccess import preprocessing, utils
from geohealthaccess.config import load_config


def preprocess_land_cover(src_dir, dst_dir, dst_crs, dst_bounds,
                          dst_res, remove=False, process_discrete=True):
    """Merge and reproject land cover tiles.

    Parameters
    ----------
    src_dir : str
        Path to source directory where land cover layers are stored.
    dst_dir : str
        Path to output directory. Output land cover stack will be
        written in the 'landcover.tif' file.
    dst_crs : dict-like CRS object
        Target coordinate reference system.
    dst_bounds : tuple of float
        Output bounds (xmin, ymin, xmax, ymax) in target CRS.
    dst_res : int or float
        Output spatial resolution in target CRS units.
    remove : bool, optional
        If set to True, raw input data will be deleted after preprocessing.
        Defaults to False.
    process_discrete : bool, optional
        If set to True, discrete classification will also be preprocessed.
        Defaults to True.
    """
    LANDCOVERS = ['bare', 'crops', 'grass', 'moss', 'shrub', 'snow',
                  'tree', 'urban', 'water-permanent', 'water-seasonal']
    # Get list of available rasters in src_dir
    filenames = [os.path.join(src_dir, f) for f in os.listdir(src_dir)
                 if f.endswith('.tif')]

    dst_filename = os.path.join(dst_dir, 'landcover.tif')
    preprocessed = []
    if not os.path.isfile(dst_filename):
        for landcover in LANDCOVERS:
            # Merge raster tiles
            name = f'{landcover}-coverfraction-layer'
            tiles = [f for f in filenames if name in f]
            merged = os.path.join(dst_dir, f'landcover_{landcover}_merged.tif')
            reprojected = merged.replace('_merged.tif', '_reprojected.tif')
            if os.path.isfile(reprojected):
                continue
            preprocessing.merge_tiles(tiles, merged, nodata=-1)
            output = preprocessing.reproject_raster(
                src_raster=merged,
                dst_filename=reprojected,
                dst_crs=dst_crs,
                resample_algorithm='bilinear',
                dst_bounds=dst_bounds,
                dst_res=dst_res,
                dst_nodata=-1,
                dst_dtype='float32')
            preprocessed.append(output)
            os.remove(merged)
        stack = os.path.join(dst_dir, 'landcover.tif')
        preprocessing.create_landcover_stack(dst_dir, stack)

    # Preprocess discrete classification if required
    if process_discrete:
        tiles = [f for f in filenames if 'discrete-classification_' in f]
        merged = os.path.join(dst_dir, 'landcover_discrete-classification_merged.tif')
        reprojected = merged.replace('_merged.tif', '.tif')
        if not os.path.isfile(reprojected):
            preprocessing.merge_tiles(tiles, merged, nodata=-1)
            output = preprocessing.reproject_raster(
                src_raster=merged,
                dst_filename=reprojected,
                dst_crs=dst_crs,
                resample_algorithm='mode',
                dst_bounds=dst_bounds,
                dst_res=dst_res,
                dst_nodata=-1,
                dst_dtype='int16')
            os.remove(merged)
    
    # Remove individual files
    for filename in preprocessed:
        os.remove(filename)
    
    # Remove raw input data
    if remove:
        for filename in os.listdir(src_dir):
            os.remove(os.path.join(src_dir, filename))

    return


def preprocess_elevation(src_dir, dst_dir, dst_crs,
                         dst_bounds, dst_res, remove=False):
    """Merge and reproject SRTM elevation tiles and compute
    slope (TODO).

    Parameters
    ----------
    src_dir : str
        Path to source directory where SRTM tiles are stored.
    dst_dir : str
        Path to output directory.
    dst_crs : dict-like CRS object
        Target coordinate reference system.
    dst_bounds : tuple of float
        Output bounds (xmin, ymin, xmax, ymax) in target CRS.
    dst_res : int or float
        Output spatial resolution in target CRS units.
    remove : bool, optional
        If set to True, delete raw input data after preprocessing.
    """
    preprocessed = os.path.join(dst_dir, 'elevation.tif')
    if os.path.isfile(preprocessed):
        return
    filenames = [os.path.join(src_dir, f) for f in os.listdir(src_dir)
                 if f.endswith('.hgt')]
    merged = os.path.join(dst_dir, 'elevation_merged.tif')
    preprocessing.merge_tiles(filenames, merged, nodata=-32768)
    preprocessing.reproject_raster(
        src_raster=merged,
        dst_filename=preprocessed,
        dst_crs=dst_crs,
        resample_algorithm='bilinear',
        dst_bounds=dst_bounds,
        dst_res=dst_res,
        dst_nodata=-32768,
        dst_dtype='float32')

    # Remove intermediary files
    os.remove(merged)

    # Remove raw input data
    if remove:
        for filename in os.listdir(src_dir):
            os.remove(os.path.join(src_dir, filename))

    return


def preprocess_water(src_dir, dst_dir, dst_crs,
                     dst_bounds, dst_res, remove=False):
    """Merge and reproject GSW tiles.

    Parameters
    ----------
    src_dir : str
        Path to source directory where GSW tiles are stored.
    dst_dir : str
        Path to output directory.
    dst_crs : dict-like CRS object
        Target coordinate reference system.
    dst_bounds : tuple of float
        Output bounds (xmin, ymin, xmax, ymax) in target CRS.
    dst_res : int or float
        Output spatial resolution in target CRS units.
    remove : bool, optional
        If set to True, delete raw input data after preprocessing.
    """
    preprocessed = os.path.join(dst_dir, 'surface_water.tif')
    if os.path.isfile(preprocessed):
        return
    filenames = [os.path.join(src_dir, f) for f in os.listdir(src_dir)
                 if f.endswith('.tif')]
    merged = os.path.join(dst_dir, 'surface_water_merged.tif')
    preprocessing.merge_tiles(filenames, merged, nodata=255)
    preprocessing.reproject_raster(
        src_raster=merged,
        dst_filename=preprocessed,
        dst_crs=dst_crs,
        resample_algorithm='bilinear',
        dst_bounds=dst_bounds,
        dst_res=dst_res,
        dst_nodata=-32768,
        dst_dtype='float32')
    os.remove(merged)

    if remove:
        for filename in os.listdir(src_dir):
            os.remove(os.path.join(src_dir, filename))

    return


def preprocess_population(src_dir, dst_dir, dst_crs,
                          dst_bounds, dst_res):
    """Reproject WorldPop data.

    Parameters
    ----------
    src_dir : str
        Path to source directory.
    dst_dir : str
        Path to output directory.
    dst_crs : dict-like CRS object
        Target coordinate reference system.
    dst_bounds : tuple of float
        Output bounds (xmin, ymin, xmax, ymax) in target CRS.
    dst_res : int or float
        Output spatial resolution in target CRS units.
    """
    filename = [os.path.join(src_dir, f) for f in os.listdir(src_dir)
                if f.endswith('.tif') and 'ppp' in f][0]
    reprojected = os.path.join(dst_dir, 'population.tif')
    if os.path.isfile(reprojected):
        return
    preprocessing.reproject_raster(
        src_raster=filename,
        dst_filename=reprojected,
        dst_crs=dst_crs,
        resample_algorithm='bilinear',
        dst_bounds=dst_bounds,
        dst_res=dst_res,
        dst_nodata=-32768,
        dst_dtype='float32')
    return


def preprocess(src_dir, dst_dir, country, dst_crs, dst_res, remove=False):
    """Preprocess input data. Merge tiles, reproject to common
    grid, mask invalid areas, and ensure correct raster compression
    and tiling.

    Parameters
    ----------
    src_dir : str
        Main input directory (raw data).
    dst_dir : str
        Output directory.
    country : str
        Three-letters code of the country of interest.
    dst_crs : str
        Target CRS.
    dst_res : int or float
        Target spatial resolution in CRS units.
    remove : bool, optional
        If True, raw input data will be deleted after preprocessing.
    """
    os.makedirs(dst_dir, exist_ok=True)
    
    print('Creating raster grid...')
    geom = utils.country_geometry(country)
    dst_crs = CRS.from_string(dst_crs)
    _, _, _, dst_bounds = preprocessing.create_grid(
        geom, dst_crs, dst_res)
    
    print('Preprocessing land cover data...')
    preprocess_land_cover(
        src_dir=os.path.join(src_dir, 'land_cover'),
        dst_dir=dst_dir,
        dst_crs=dst_crs,
        dst_bounds=dst_bounds,
        dst_res=dst_res,
        remove=remove)
    
    print('Preprocessing elevation data...')
    preprocess_elevation(
        src_dir=os.path.join(src_dir, 'elevation'),
        dst_dir=dst_dir,
        dst_crs=dst_crs,
        dst_bounds=dst_bounds,
        dst_res=dst_res,
        remove=remove)
    
    print('Preprocessing surface water data...')
    preprocess_water(
        src_dir=os.path.join(src_dir, 'water'),
        dst_dir=dst_dir,
        dst_crs=dst_crs,
        dst_bounds=dst_bounds,
        dst_res=dst_res,
        remove=remove)
    
    print('Preprocessing population data...')
    preprocess_population(
        src_dir=os.path.join(src_dir, 'population'),
        dst_dir=dst_dir,
        dst_crs=dst_crs,
        dst_bounds=dst_bounds,
        dst_res=dst_res)
    
    print('Masking data outside country boundaries...')
    for filename in os.listdir(dst_dir):
        if filename.endswith('.tif'):
            preprocessing.mask_raster(os.path.join(dst_dir, filename),
                                      country)

    print('Done!')
    return


def main():
    # Parse command-line arguments & load configuration
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file',
                        type=str,
                        help='.ini configuration file')
    parser.add_argument('--remove',
                        action='store_true',
                        help='remove raw data from disk after preprocessing')
    args = parser.parse_args()
    conf = load_config(args.config_file)
    input_dir = os.path.abspath(conf['DIRECTORIES']['InputDir'])
    interm_dir = os.path.abspath(conf['DIRECTORIES']['IntermDir'])

    # Run script
    preprocess(src_dir=input_dir,
               dst_dir=interm_dir,
               country=conf['AREA']['CountryCode'],
               dst_crs=conf['AREA']['CRS'],
               dst_res=float(conf['AREA']['Resolution']),
               remove=args.remove)

if __name__ == '__main__':
    main()
