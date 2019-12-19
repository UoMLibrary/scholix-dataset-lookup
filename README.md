# scholix-dataset-lookup
Find dataset DOIs from the Scholix API based on a list of target publication DOIs (e.g. from a CRIS system).

## About this script

This script requires Python 3 with the `requests`, `pandas` and `openpyxl` modules. You can Install these modules using pip.

## Preparing your data

See the example input data `input_dois.xlsx`. This was a list of DOIs generated from a Scopus query.

## Output data

A new file `output.xlsx` will be generated with the Dataset DOIs and Dataset Titles returned by the Scholix API. Note that this file can contain duplicate DOIs (where Scholix returned multiple links).

## Example usage:

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
