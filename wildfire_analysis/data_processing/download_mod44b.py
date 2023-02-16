import json
import os
import requests
import sys
from pathlib import Path

from tqdm import tqdm

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

verbose = False
if (sys.argv[-1] == "--verbose"):
    verbose = True

token = os.environ.get('TOKEN')

request_meta = root_dir / '../tmp/mod44b_request_submission.json'
dest_dir = root_dir / '../data/raw/veg/mod44b'

with open(request_meta, 'r') as jsonfile:
    meta = json.load(jsonfile)
    task_id = meta['task_id']

response = requests.get(
    'https://appeears.earthdatacloud.nasa.gov/api/bundle/{0}'.format(task_id),  
    headers={'Authorization': 'Bearer {0}'.format(token)}
)

bundle_response = response.json()
files = bundle_response['files']

with tqdm(total=len(files),disable=not verbose) as pbar: # for progress bar

    for f in files:

        fid = f['file_id']

        response = requests.get( 
            'https://appeears.earthdatacloud.nasa.gov/api/bundle/{0}/{1}'.format(task_id,fid),
            headers={'Authorization': 'Bearer {0}'.format(token)}, 
            allow_redirects=True,
            stream=True
        )

        export_filename = dest_dir / Path(f['file_name']).name

        # write the file to the destination directory
        with open(export_filename, 'wb') as fn:
            for data in response.iter_content(chunk_size=8192):
                fn.write(data)

        pbar.update()