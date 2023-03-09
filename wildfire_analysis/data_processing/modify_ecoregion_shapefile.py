from pathlib import Path

import geopandas as gpd

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

# Ecoregion IDs to keep in study area. Predetermined from evaluation of 
# ecoregions map
ecos_to_keep = {'ECO_ID': [50602.0,50603.0,50604.0,50605.0,50606.0,50607.0,
    50608.0,50609.0,50610.0,50612.0,50613.0,50614.0,50616.0,50617.0,51111.0]}

# Read in shapefile with ecoregion perimeters ('ecos') and a shapefile with 
# polygons to ultimately remove from study area. The polygons to remove were
# identified and exported using QGIS 3.28.
fn = root_dir / '../data/raw/ecoregions/official/wwf_terr_ecos.shp'
ecos = gpd.read_file(fn)
poly_to_remove = gpd.read_file(root_dir/ '../data/ancillary/to_remove_east_can.shp')

# Subset world ecoregions map to those only in study area.
match_ecos_id = ecos.isin(ecos_to_keep)
match_ecos_id = match_ecos_id.ECO_ID.values # Get T/F indices
ecos_subset = ecos.loc[match_ecos_id]

# Remove specific polygons based on OBJECTID from subseted ecoregions data frame.
poly_to_remove_id = ecos_subset.isin(poly_to_remove['OBJECTID'].values)
poly_to_remove_id = poly_to_remove_id['OBJECTID'].values
ecos_subset = ecos_subset.loc[~poly_to_remove_id,:]

# Manually relabel/reclassify several ecoregions. These are smaller ecoregions 
# that are aggregated and combined with larger ones.
ecos_subset.loc[ecos_subset.ECO_ID == 50603.0,'ECO_NUM'] = 7.0
ecos_subset.loc[ecos_subset.ECO_ID == 50603.0,'ECO_NAME'] = 'Interior Alaska-Yukon lowland taiga'
ecos_subset.loc[ecos_subset.ECO_ID == 50603.0,'ECO_ID'] = 50607.0

ecos_subset.loc[ecos_subset.ECO_ID == 50604.0,'ECO_NUM'] = 7.0
ecos_subset.loc[ecos_subset.ECO_ID == 50604.0,'ECO_NAME'] = 'Interior Alaska-Yukon lowland taiga'
ecos_subset.loc[ecos_subset.ECO_ID == 50604.0,'ECO_ID'] = 50607.0

ecos_subset.loc[ecos_subset.ECO_ID == 50617.0,'ECO_NUM'] = 13.0
ecos_subset.loc[ecos_subset.ECO_ID == 50617.0,'ECO_NAME'] = 'Northern Cordillera forests'
ecos_subset.loc[ecos_subset.ECO_ID == 50617.0,'ECO_ID'] = 50613.0

# Use dissolve method to aggregate ecoregions together by ECO_ID
ecos_subset = ecos_subset.dissolve(by='ECO_ID',as_index=False)

# Export ecoregions map for use in analysis.
ecos_subset.to_file(root_dir / '../data/processed/ecoregions/ecos.shp')