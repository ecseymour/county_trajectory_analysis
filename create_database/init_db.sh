#!/bin/bash
# WARNING: THIS WILL OVERWRITE AN EXISTING DATABASE
# create Spatialite DB using county shapefile
db="$(dirname "$0")/../../output/db.sqlite"

fp="$(dirname "$0")/../../data/nhgis0013_shapefile_tl2010_us_county_2010/US_county_2010.shp"

# read 2010 counties shp into db
ogr2ogr -f 'SQLite' -dsco SPATIALITE=YES \
-t_srs http://spatialreference.org/ref/esri/102003/ \
$db $fp \
-nlt PROMOTE_TO_MULTI

# add index on gisjoin field
sqlite3 $db 'CREATE INDEX idx_uscounty2010_gisjoin ON US_county_2010(GISJOIN);'
sqlite3 $db 'CREATE INDEX idx_uscounty2010_geoid10 ON US_county_2010(GEOID10);'

# read 2010 counties shp into db
fp="$(dirname "$0")/../../data/tl_2010_us_county10/tl_2010_us_county10.shp"
ogr2ogr -f 'SQLite' -update \
-t_srs http://spatialreference.org/ref/esri/102003/ \
$db $fp \
-nlt PROMOTE_TO_MULTI

sqlite3 $db 'CREATE INDEX idx_tl2010uscounty10_geoid10 ON tl_2010_us_county10(GEOID10);'

# read counties polygon shp into db
fp="$(dirname "$0")/../../data/gz_2010_us_050_00_20m/gz_2010_us_050_00_20m.shp"
ogr2ogr -f 'SQLite' -update \
-t_srs http://spatialreference.org/ref/esri/102003/ \
$db $fp \
-nlt PROMOTE_TO_MULTI

# read states polygon shp into db
fp="$(dirname "$0")/../../data/gz_2010_us_040_00_20m/gz_2010_us_040_00_20m.shp"
ogr2ogr -f 'SQLite' -update \
-t_srs http://spatialreference.org/ref/esri/102003/ \
$db $fp \
-nlt PROMOTE_TO_MULTI


echo "done"