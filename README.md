# GeoHealthAccess

* [Description](#description)
* [Installation](#installation)
* [Usage](#usage)
  + [Data acquisition](#data-acquisition)
  + [Preprocessing](#preprocessing)
  + [Modeling](#modeling)
* [Example](#example)
* [Docker](#docker)
* [Methodology](#methodology)
* [Authors](#authors)

## Description

![Accessibility map](https://raw.githubusercontent.com/BLSQ/geohealthaccess/master/docs/images/travel-times-example.png)

Modeling population accessibility to health facilities has always been
tedious and time-consuming. From the selection of relevant data sources
to the modeling in itself, a wide range of skills and software solutions
are required. GeoHealthAccess is a tool that aims to automate the process
using a set of high resolution, global and open datasets -- in order to
enable fast and automated country-scaled analysis. To that end, input datasets
are automatically pulled from various sources:

* [Geofabrik](https://www.geofabrik.de) (OpenStreetMap) for the transport network ;
* [Copernicus Global Land Cover](https://lcviewer.vito.be/) for land cover ;
* [Global Surface Water](https://global-surface-water.appspot.com/) for surface water ;
* [Shuttle Radar Topography Mission](https://www2.jpl.nasa.gov/srtm/) for topography ;
* and [WorldPop](https://www.worldpop.org/) for population maps.

## Installation

GeoHealthAccess have three system dependencies: `gdal` is used to process raster
data, `osmium-tool` to process OpenStreetMap data and `grass` to perform a cost
distance analysis. Alternatively, a docker image is also available (see below).

``` sh
# Ubuntu 20.04
apt-get install gdal-bin osmium-tool grass-core
```

The python package can then be installed using pip:

``` sh
# Download source code
git clone https://github.com/BLSQ/geohealthaccess
cd geohealthaccess
pip install -e .

# To install devevelopment dependencies such as pytest, use:
pip install -e .[dev]
```

## Usage

The `geohealthaccess` program is divided into three commands:

* `download` for automatic data acquisition
* `preprocess` for preprocessing of input data
* `access` to compute travel times

``` sh
geohealthaccess --help
```

```
Usage: geohealthaccess [OPTIONS] COMMAND [ARGS]...

  Map accessibility to health services.

Options:
  --help  Show this message and exit.

Commands:
  access      Map travel times to the provided health facilities.
  download    Download input datasets.
  preprocess  Preprocess and co-register input datasets.
```

### Data acquisition

NASA EarthData credentials are required to download SRTM tiles. An account can
be created [here](https://urs.earthdata.nasa.gov/users/new).

``` sh
geohealthaccess download --help
```

```
Usage: geohealthaccess download [OPTIONS]

  Download input datasets.

Options:
  -c, --country TEXT         ISO A3 country code  [required]
  -o, --output-dir PATH      Output directory
  -u, --earthdata-user TEXT  NASA EarthData username  [required]
  -p, --earthdata-pass TEXT  NASA EarthData password  [required]
  -f, --overwrite            Overwrite existing files
  --help                     Show this message and exit.
```

If `output-dir` is not provided, files will be written to `./Data/Input`.

NASA EarthData credentials can also be set using environment variables:

``` sh
export EARTHDATA_USERNAME=<your_username>
export EARTHDATA_PASSWORD=<your_password>
```

### Preprocessing

``` sh
geohealthaccess preprocess --help
```

```
Usage: geohealthaccess preprocess [OPTIONS]

  Preprocess and co-register input datasets.

Options:
  -c, --country TEXT      ISO A3 country code  [required]
  -s, --crs TEXT          CRS as a PROJ4 string  [required]
  -r, --resolution FLOAT  Pixel size in `crs` units
  -i, --input-dir PATH    Input data directory
  -o, --output-dir PATH   Output data directory
  -f, --overwrite         Overwrite existing files
  --help                  Show this message and exit.
```

If not specified, `input-dir` will be set to `./Data/Input` and `output-dir` to `./Data/Intermediary`.

### Modeling

``` sh
geohealthaccess access --help
```

```
Usage: geohealthaccess access [OPTIONS]

  Map travel times to the provided health facilities.

Options:
  -i, --input-dir PATH      Input data directory
  -o, --output-dir PATH     Output data directory
  --car / --no-car          Enable/disable car scenario
  --walk / --no-walk        Enable/disable walk scenario
  --bike / --no-bike        Enable/disable bike scenario
  -s, --travel-speeds PATH  JSON file with custom travel speeds
  -d, --destinations PATH   Destination points (GeoJSON or Geopackage)
  -f, --overwrite           Overwrite existing files
  --help                    Show this message and exit.
```

If not specified, `input-dir` is set to `./Data/Intermediary` and `output-dir`
to `./Data/Output`. By default, only the `car` scenario is enabled and if no
`destinations` are provided, health facilities extracted from OpenStreetMap will
be used as target points for the cost distance analysis. Likewise, default
values for travel speeds are used if the `--travel-speeds` option is not set.

Three output rasters are created for each enabled scenario and provided
destination points:

* `cost_<scenario>_<destinations>.tif` : cumulated cost (or travel time, in
  minutes) to reach the nearest `destinations` feature.
* `nearest_<scenario>_<destinations>.tif` : ID of the nearest `destinations`
  feature.
* and `backlink_<scenario>_<destinations>.tif` : backlink raster.

## Example

Creating a map of travel times to the nearest health facility for Burundi:

``` sh
# Download input datasets
geohealthaccess download \
	--country BDI \
	--earthdata-user <your_username> \
	--earthdata-pass <your_password>

# Preprocess input datasets to a common raster grid
geohealthaccess preprocess \
	--country BDI \
	--crs "EPSG:3857" \
	--resolution 100

# Compute travel times to nearest health facility for the `car` and `walk`
# scenarios.
geohealthaccess access --car --walk

# Or use your own data for destinations:
geohealthaccess access --car --walk -d hospitals.geojson -d clinics.geojson
```

## Docker

A docker image is available on [Docker
Hub](https://hub.docker.com/r/yannforget/geohealthaccess).

``` sh
cd <project_dir>
docker run -v $(pwd):/project:rw yannforget/geohealthaccess:latest
```

## Methodology

![Processing chain](/docs/images/processing-chain.png)
: Processing chain (red=input, yellow=intermediary, green=output).

## Authors

The GeoHealthAccess project is funded by [Innoviris](https://innoviris.brussels/)
and led by a partnership between [Bluesquare](https://bluesquarehub.com/) and
the [Spatial Epidemiology Lab](https://spell.ulb.be/) (Université Libre de Bruxelles).
The project is based on a previous work from [IGEAT-ANAGEO](http://igeat.ulb.ac.be/en/introduction/)
(Université Libre de Bruxelles) and the
[Department of Geography](https://www.unamur.be/en/sci/geography) (University of Namur)
in the [She Decides](https://github.com/yannforget/shedecides) project.

* Grégoire Lurton (Bluesquare)
* Yann Forget (Spatial Epidemiology Lab, Université Libre de Bruxelles)
* Moritz Lennert (IGEAT-ANAGEO, Université Libre de Bruxelles)
* Sabine Vanhuysse (IGEAT-ANAGEO, Université Libre de Bruxelles)
* Taïs Grippa (IGEAT-ANAGEO, Université Libre de Bruxelles)
* Catherine Linard (Department of Geography, University of Namur)
