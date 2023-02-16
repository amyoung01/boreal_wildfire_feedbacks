import json
from pathlib import Path

from wildfire_analysis.utils import helpers as h

root_dir = Path(h.get_root_dir())

# read file
with open(root_dir / '../tmp/mod44b_request_meta.json', 'r') as json_info:
    meta = json_info.read()

# parse file
obj = json.loads(meta)
obj = obj[0]
task_id = obj['task_id']

if __name__ == '__main__':

    print(task_id)