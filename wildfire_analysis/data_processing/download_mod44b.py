import json
import os
import requests
import sys
import time
from pathlib import Path

from tqdm import tqdm

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

verbose = False
if (sys.argv[-1] == "--verbose"):
    verbose = True

token = os.environ.get('EARTHDATA_TOKEN')

status_response = True

while status_response:

    response = requests.get(
        'https://appeears.earthdatacloud.nasa.gov/api/status', 
        headers={'Authorization': 'Bearer {0}'.format(token)})
    status_response = response.json()

    localtime = time.localtime()
    localtime_str = time.strftime("%I:%M:%S %p", localtime)
    print('Checked at %s, still processing request ...' % localtime_str,
          end="\r")

    time.sleep(60*5)

print('Request has finished at %s!' % time.strftime('%I:%M:%S %p', localtime))
print('\nNow downloading ...')

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