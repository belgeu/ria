# ria
Auto ria CLI

## Install RIA CLI
`pip3 install -r requirements.txt`

## Set API key
* Get key
https://developers.ria.com/
* Initialize
```
./run.py -k [RIA_API_KEY]
```

## Configuration
Default configuration values are stored into `config/ria.ini` on script start.
### Ria configuration

- `search_results_location` - Folder to store search results. Default is "results/".
- `cache_files_location` - Folder to store cache files. Default is "tmp/".
- `cache_expiry_time` - Cache expiration time. Default is 1 hour.
- `output_format` - Search output. Default is "csv".


### Fields to extract
Change ordering as desired to change column placement in the output file.

```
[OUTPUT]
fields = id,title,year,mileage,price(uah),price(usd),price(eur),fuel,gearbox,city,region,type,url,phone,created,updated,sold,exchange,description
```

## Example queries
Required options: 
* -m, --make

Get list of cars available to search:
```
./run.py -get all-cars
```
Get list of models for specific car make:
```
./run.py -get all-models -m Ford
```
Get list of body styles
```
./run.py -get all-styles
```
### Make search:
```
./run.py -m Ford -M Focus -b Хэтчбек -y 2000 -Y 2001 -g manual -f petrol
```
## Search results
Search result is stored into a `.csv` file following a name pattern:<br>
`{name}{model}_{count}_{time}.csv`

By default all result files are stored into `results` folder.

E.g. `results/FordFocus_25_20190819211118.csv`

File name will contain `FAILED` if search results are inconsistent or incomplete due to search errors 
(connection failures, connection limit exceeded, etc.).

E.g. `results/FordFocus_25_20190819211118_FAILED.csv`
