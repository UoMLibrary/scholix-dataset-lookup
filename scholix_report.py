import requests, pandas, time, threading, sys, itertools
from pandas import ExcelWriter

endpoint = 'http://api.scholexplorer.openaire.eu/v1'

count = itertools.count()
count_data = itertools.count()
count_no_data = itertools.count()
count_error = itertools.count()
show_progress = True

def display_progress(value, endvalue, bar_length=20):
  if not show_progress:
    return

  percent = float(value) / endvalue
  arrow = '*' * int(round(percent * bar_length)-1) + '*'
  spaces = ' ' * (bar_length - len(arrow))
  sys.stdout.write("\rDownloading [{0}] {1}%".format(arrow + spaces, int(round(percent * 100))))
  sys.stdout.flush()

def fetch(session, input, output, offset, stride, fetch_function):
  global count

  index = offset
  while index < len(input):
    input_value = input[index]

    progress = next(count)
    if progress % (len(input)//100) == 0:
      display_progress(progress, len(input))
    fetch_function(session, input_value, output)
    index += stride

def fetch_multithreaded(input, thread_count, fetch_function):

  total = len(input)
  output = {}

  start = time.time()

  for thread_id in range(thread_count):
    session = requests.session()
    thread = threading.Thread(target=fetch, args=(session, input, output, thread_id, thread_count, fetch_function))
    thread.start()

  for thread in threading.enumerate():
    if thread != threading.current_thread():
      thread.join()
  display_progress(total, total)

  end = time.time()
  elapsed = end - start

  print('\r\nProcessed {0} requests in {1} seconds ({2} requests/second)'.format(total, int(elapsed), int(total//elapsed)))
  print('{0} DOIs found, {1} DOIs had no data, {2} DOIs had errors'.format(next(count_data), next(count_no_data), next(count_error)))

  return output

def process_doi(session, doi, output):
  global count_data, count_no_data, count_error
  url = endpoint + '/linksFromPid?pid=' + doi + '&pidType=doi'
  try:
    response = session.get(url)
    if response.status_code == 200:
      output[doi] = parse_result(doi, response.json())
      next(count_data)
    else:
      output[doi] = None
      next(count_no_data)
  except requests.exceptions.RequestException as e:
    print(e)
    output[doi] = None
    next(count_error)
  except:
    output[doi] = None
    next(count_error)

def parse_result(doi, data):
  result = None
  if data is not None:
    result = data
    
  return result

# Get input DOIs from excel file
df = pandas.read_excel('input_dois.xlsx')
raw_doi_list = df['DOI'].tolist()
doi_list = list(set(raw_doi_list))

print('Loaded {0} unique DOIs ({1} total)'.format(len(doi_list), len(raw_doi_list)))

# Degree of parallelism
thread_count = 8

print('Starting {0} threads'.format(thread_count))

results = fetch_multithreaded(doi_list, thread_count, process_doi)

dataset_dois = []

for doi in doi_list:
  result = results[doi]
  if (result != None):
    for dataset in result:
      for i in dataset['target']['identifiers']:
        if (i['schema'] == 'doi'):
          dataset_doi = 'https://doi.org/' + i['identifier']
          dataset_title = ''
          if 'title' in dataset['target'].keys():
            dataset_title = dataset['target']['title']
          dataset_dois.append({'doi': doi, 'dataset_title': dataset_title, 'dataset_doi': 'https://doi.org/' + i['identifier']})

print('Found {0} dataset DOIs'.format(len(dataset_dois)))

# Create the output file
output_filename = 'output.xlsx'
print('Writing output file "{0}"'.format(output_filename))
writer = ExcelWriter(output_filename)

# Convert dictionaries to to a dataframes and write them to excel tabs

summary_df = pandas.DataFrame(dataset_dois)
summary_df.to_excel(writer, 'DOI List ({0})'.format(len(dataset_dois)), columns=['doi', 'dataset_title', 'dataset_doi'])

writer.save()
