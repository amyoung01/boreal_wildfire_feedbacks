import json
from pathlib import Path

import yaml

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

# Import config file and read in parameters needed for data processing
# Get global values from configuration file
config_fn = root_dir / 'config.yaml'

with open(config_fn,'r') as config_file:   
    config_params = yaml.safe_load(config_file)

    geo_lims = config_params['EXTENT']['mod44b_download_lims']
    treecov_yr =config_params['TIME']['treecov_yr']

dictionary = {
    'params': {
        'geo': {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [
                        [
                            [geo_lims[0], geo_lims[1]],
                            [geo_lims[0], geo_lims[3]],
                            [geo_lims[2], geo_lims[3]],
                            [geo_lims[2], geo_lims[1]],
                            [geo_lims[0], geo_lims[1]]
                        ]
                    ]    
                },
                'properties': {}
            }]
        },
        'dates': [{
            'endDate': '12-31-%d' % treecov_yr[1],
            'startDate': '01-01-%d' % treecov_yr[0],
            'recurring': False,
            'yearRange': [1950,2050]
        }],
        'layers': [{
            'layer': 'Percent_Tree_Cover',
            'product': 'MOD44B.006'
            }, {
            'layer': 'Quality',
            'product': 'MOD44B.006'
            }, {
            'layer': 'Percent_NonTree_Vegetation',
            'product': 'MOD44B.006'
            }, {
            'layer': 'Percent_NonVegetated',
            'product': 'MOD44B.006'
            }, {
            'layer': 'Cloud',
            'product': 'MOD44B.006'
            }],
        'output': {
            'format': {
                'type': 'geotiff'
            },
            'projection': 'sinu_modis'
        }
    },
    'task_name': 'MOD44B_Alaska_and_Canada',
    'task_type': 'area'
}

# Serializing json
json_object = json.dumps(dictionary, indent = 2, separators=(',', ':'))
 
export_fn = str(root_dir / 'nasa_mod44b_request.json')
# Writing to sample.json
with open(str(export_fn), 'w') as f:
    f.write(json_object)