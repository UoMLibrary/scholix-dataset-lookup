# scholix-dataset-lookup
Find dataset DOIs from the Scholix API based on a list of target publication DOIs (e.g. from a CRIS system). The dataset DOIs can be looked up in DataCite to retrieve the dataset metadata (where it exists).

Please note that the datacite script uses the [DataCite v1 API](https://support.datacite.org/docs/api-v1) rather than the newer [DataCite v2 API](https://support.datacite.org/docs/api), so this code could likely be simplified.

## About these scripts

These scripts require Python 3 with the `requests`, `requests_cache`, `pandas`, `xmltodict` and `openpyxl` modules. You can Install these modules using pip.

DataCite API results are cached in a file called `datacite_api_cache.sqlite`. Where DataCite does not have any information about a DOI (e.g. because it may not actually be a dataset) you will see 404 errors.

## Preparing your data

See the example input data `input_dois.xlsx`. This was a list of DOIs generated from a Scopus query.

## Output data

### scholix_report.py
A new file `output.xlsx` will be generated with the Dataset DOIs and Dataset Titles returned by the Scholix API. Note that this file can contain duplicate DOIs (where Scholix returned multiple links).

### datacite.py
A new file `output_datasets.xlsx` will be generated with a summary of the DOIs which could be found in the DataCite v1 works API. An HTML export of each DOI (key fields only) will also be generated in the datasets_html folder.

## Example usage:

### Initial scholix lookup using DOI spreadsheet

```
$ python3 scholix_report.py 

Loaded 500 unique DOIs (500 total)
Starting 8 threads
Downloading [********************] 100%
Processed 500 requests in 6 seconds (79 requests/second)
500 DOIs found, 0 DOIs had no data, 0 DOIs had errors
Found 644 dataset DOIs
Writing output file "output.xlsx"
```

### Retrieving further dataset details from DataCite v1 API

```
python3 datacite.py 

952 unique dataset DOIs (952 total)

...

https://api.datacite.org/works/10.1136/bmj.327.7417.708

	title: Rapid tranquillisation for agitated patients in emergency psychiatric rooms: a randomised trial of midazolam versus haloperidol plus promethazine
	published: 2003
	authors: 1

...

Writing output file "output_datasets.xlsx"
```
