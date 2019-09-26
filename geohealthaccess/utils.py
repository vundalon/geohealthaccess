import json
import os
from ftplib import FTP
from pkg_resources import resource_string
from urllib.parse import urlparse

import requests
from shapely.geometry import shape
from tqdm.auto import tqdm


def country_geometry(country):
    """Get the shapely geometry corresponding to a given country
    identified by its name or its three-letters ISO A3 Code.
    """
    countries = json.loads(
        resource_string(__name__, 'resources/countries.geojson'))
    geom = None
    for feature in countries['features']:
        name = feature['properties']['ADMIN']
        code = feature['properties']['ISO_A3']
        if country in (name, code):
            geom = shape(feature['geometry'])
    if not geom:
        raise ValueError('Country not found.')
    return geom


def download_from_url(session, url, output_dir, show_progress=True,
                      overwrite=False):
    """Download remote file from URL in a given requests session.

    Params
    ------
    session : requests.Session()
        An authentified requests session object.
    url : str
        Full URL of the file to be downloaded.
    output_dir : str
        Path to output directory. Local filename is guessed from the URL.
    show_progress : bool, optional (default=True)
        Show a progress bar.
    overwrite : bool, optional (default=False)
        If set to `False`, local files will not be overwritten if they have
        the same size as the remote file.

    Returns
    -------
    local_path : str
        Local path to downloaded file.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = url.split('/')[-1]
    local_path = os.path.join(output_dir, filename)
    with session.get(url, stream=True) as r:
        r.raise_for_status()
        file_size = int(r.headers['Content-Length'])
        if os.path.isfile(local_path) and not overwrite:
            if os.path.getsize(local_path) == file_size:
                return local_path
        if show_progress:
            progress_bar = tqdm(
                desc=filename, total=file_size, unit_scale=True, unit='B')
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    if show_progress:
                        progress_bar.update(1024)
        if show_progress:
            progress_bar.close()
    return local_path


def download_from_ftp(url, output_dir, overwrite=False):
    """Download a file from a public FTP server.

    Parameters
    ----------
    url : str
        Path to remote file (ftp://<ftp_server>/<dir>/<file>).
    output_dir : str
        Path to local output directory.
    overwrite : bool, optional
        Overwrite local file.
    
    Returns
    -------
    local_path : str
        Local path to downloaded file.
    """
    url = urlparse(url)
    ftp = FTP(url.netloc)
    ftp.login()
    parts = url.path.split('/')
    filename = parts[-1]
    directory = '/'.join(parts[-2]) + '/'
    ftp.cwd(directory)
    filesize = ftp.size(filename)
    progress = tqdm(total=filesize, desc=filename, unit_scale=True, unit='B')
    local_path = os.path.join(output_dir, filename)

    with open(local_path, 'wb') as f:

        def write_and_progress(chunk):
            """Custom callback function that write data chunk to disk
            and update the progress bar accordingly.
            """
            f.write(chunk)
            progress.update(len(chunk))
        
        ftp.retrbinary(f'RETR {filename}', write_and_progress)
    
    progress.close()
    ftp.close()
    return local_path
