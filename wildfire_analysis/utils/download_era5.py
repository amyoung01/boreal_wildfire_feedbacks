from pathlib import Path
import yaml

import cdsapi

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

config_fn = root_dir / 'config.yaml'

with open(config_fn,'r') as config_file:
    config_params = yaml.safe_load(config_file)

    era5_yr = config_params['TIME']['era5_yr']
    geolims = config_params['EXTENT']['geog_lims']

vars = [
    '2m_dewpoint_temperature',
    '2m_temperature',
    '10m_u_component_of_wind', 
    '10m_v_component_of_wind',
    'total_precipitation'
    ]
    
yr = range(era5_yr[0],era5_yr[1]+1)
mon = range(1,12+1)

for v in range(0,len(vars)):
    
    for y in range(0,len(yr)):
                            
        fn = '%d_era5_reanalysis_%s.nc' % (yr[y],vars[v])
        fn = root_dir.joinpath('../tmp',fn)

        c = cdsapi.Client()
        
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': vars[v],
                'year': str(yr[y]),
                'month': [
                        '1','2','3',
                        '4','5','6',
                        '7','8','9',
                        '10','11','12'
                        ],
                'day': [
                        '1','2','3','4','5','6','7','8','9','10',
                        '11','12','13','14','15','16','17','18','19','20',
                        '21','22','23','24','25','26','27','28','29','30',
                        '31'
                        ],
                'time': [
                         '00:00','01:00','02:00','03:00','04:00','05:00',
                         '06:00','07:00','08:00','09:00','10:00','11:00',
                         '12:00','13:00','14:00','15:00','16:00','17:00',
                         '18:00','19:00','20:00','21:00','22:00','23:00',
                         ],
                'area': [geolims[3],geolims[0],geolims[1],geolims[2]],
            },
            fn)
