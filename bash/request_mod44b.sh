# Read in user provided token as first positional argument. Tokens expire every
# 48 hours. Directions on how to acquire token given earthdata login are 
# available here: https://appeears.earthdatacloud.nasa.gov/api/
export TOKEN=$1

# Set up directory names

# Find directory of current file, source: https://stackoverflow.com/a/246128
WDIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Run file to generate json file providing the data needed for the request
cd $WDIR/../wildfire_analysis/utils
python generate_mod44b_json.py

# Location of json file
JSONFILE=$WDIR/../wildfire_analysis/nasa_mod44b_request.json

# Set destination directory 
DEST=$WDIR/../data/raw/veg/mod44b
mkdir -p $DEST

# Submit processing reques to NASA AppEEARS (https://appeears.earthdatacloud.nasa.gov)
# Download metadata from processing into json file. This will give task_id 
# which is needed for downloading
curl \
  --request POST \
  --data @$JSONFILE \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer $TOKEN" "https://appeears.earthdatacloud.nasa.gov/api/task" \
  > $WDIR/../tmp/mod44b_request_submission.json

# Wait 5 minutes before checking status for the first time and initiating 
# download
sleep 5m

# Use python file to download each geotiff file that were processed
cd $WDIR/../wildfire_analysis/data_processing
python download_mod44b.py --verbose

rm $WDIR/../tmp/mod44b_request_submission.json

echo
echo "Finished downloading MOD44B datasets into $DEST"
