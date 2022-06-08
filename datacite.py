import pandas, requests, requests_cache, os, html, base64, xmltodict
from pandas import ExcelWriter

requests_cache.install_cache('datacite_api_cache')

input_filename = 'output.xlsx'
output_filename = 'output_datasets.xlsx'
export_dir = 'datasets_html'

def write_field_header_as_html(file, name):
	file.write('<b style="color:grey;">')
	file.write(html.escape(name))
	file.write('</b>')
	file.write('<br>')

def write_field_as_html_input(file, value, rows):
	file.write('<textarea rows="{}" cols="120" readonly onclick="this.focus();this.select()">'.format(rows))
	if value is not None:
		file.write(html.escape(str(value)))
	file.write('</textarea>')
	file.write('<br>')
	file.write('<br>')

def write_field_as_html_input_single(file, metadata, name, rows):
	if (name in metadata.keys()):
		write_field_as_html_input(file, metadata[name], rows)

def render(doi, metadata, publications):
	prefix_start = doi.find('10.')
	prefix_end = doi.find('/', prefix_start)
	prefix = doi[prefix_start:prefix_end]
	short_doi = doi[prefix_start:]

	if not os.path.exists(export_dir):
		os.mkdir(export_dir)

	dir_path = os.path.join(export_dir, prefix)
	if not os.path.exists(dir_path):
		os.mkdir(dir_path)

	file_path = os.path.join(dir_path, short_doi.replace('/','-') + '.html')

	xml_text = base64.b64decode(metadata['xml'])
	xml_dict = xmltodict.parse(xml_text)
	if 'resource' in xml_dict.keys():
		xml_resource = xml_dict['resource']
	else:
		xml_resource = xml_dict['default:resource']
		print('\tXML Error - default:resource')
		return

	file = open(file_path, 'w', encoding='utf-8')

	file.write('<html><head>')
	file.write('<meta charset="UTF-8">')
	file.write('<title>Metadata for {}</title>'.format(short_doi))
	file.write('</head><body>')

	file.write('<h1>')
	file.write('<a href="https://doi.org/{}" target="_blank">'.format(short_doi))
	file.write(short_doi)
	file.write('</a>')
	file.write('</h1>')

	file.write('<h3>Title</h3>')
	write_field_as_html_input_single(file, metadata, 'title', 2)

	file.write('<h3>Description</h3>')
	write_field_as_html_input_single(file, metadata, 'description', 10)

	file.write('<h3>Date of data production</h3>')
	write_field_as_html_input_single(file, metadata, 'published', 2)

	creators = []
	if len(metadata['author']) == 1:
		creators.append(xml_resource['creators']['creator'])
	else:
		for creator in xml_resource['creators']['creator']:
			creators.append(creator)

	file.write('<h3>People - creators ({})</h3>'.format(len(creators)))

	for creator in creators:
		orcid = None
		affiliation = None
		if 'affiliation' in creator:
			if isinstance(creator['affiliation'], list):
				affiliation = '; '.join(creator['affiliation'])
			else:
				affiliation = creator['affiliation']
		if 'nameIdentifier' in creator:
			if isinstance(creator['nameIdentifier'], list):
				for identifier in creator['nameIdentifier']:
					if identifier['@nameIdentifierScheme'] == 'ORCID':
						orcid = identifier['#text']
			else:
				identifier = creator['nameIdentifier']
				if identifier['@nameIdentifierScheme'] == 'ORCID':
					orcid = identifier['#text']

		if isinstance(creator['creatorName'], str):
			creatorText = creator['creatorName']
		else:
			creatorText = creator['creatorName']['#text']

		if affiliation is not None:
				creatorText += '\nAffiliation: ' + str(affiliation)
		if orcid is not None:
			creatorText += '\nORCID: ' + orcid

		write_field_as_html_input(file, creatorText, 3)

	contributors = []
	if 'contributors' in xml_resource.keys() and xml_resource['contributors'] is not None:
		if isinstance(xml_resource['contributors']['contributor'], list):
			for contributor in xml_resource['contributors']['contributor']:
				contributors.append(contributor)
		else:
			contributors.append(xml_resource['contributors']['contributor'])

	if (len(contributors) > 0):
		file.write('<h3>People - contributors ({})</h3>'.format(len(contributors)))

	for contributor in contributors:
		orcid = None
		affiliation = None
		if 'affiliation' in contributor:
			if isinstance(contributor['affiliation'], list):
				affiliation = '; '.join(contributor['affiliation'])
			else:
				affiliation = contributor['affiliation']
		if 'nameIdentifier' in contributor:
			if isinstance(contributor['nameIdentifier'], list):
				for identifier in contributor['nameIdentifier']:
					if identifier['@nameIdentifierScheme'] == 'ORCID':
						orcid = identifier['#text']
			else:
				identifier = contributor['nameIdentifier']
				if identifier['@nameIdentifierScheme'] == 'ORCID':
					orcid = identifier['#text']

		if isinstance(contributor['contributorName'], str):
			contributorText = contributor['contributorName']
		else:
			contributorText = contributor['contributorName']['#text']

		if affiliation is not None:
			contributorText += '\nAffiliation: ' + affiliation
		if orcid is not None:
			contributorText += '\nORCID: ' + orcid

		write_field_as_html_input(file, contributorText, 3)


	file.write('<h3>Publisher</h3>')
	if ('publisher' in xml_resource.keys()):
		write_field_as_html_input_single(file, xml_resource, 'publisher', 2)

	file.write('<h3>DOI</h3>')
	write_field_as_html_input(file, doi, 2)

	file.write('<h3>Related publications ({})</h3>'.format(len(publications)))
	for publication in publications.keys():
		write_field_as_html_input(file, publication, 2)

	file.write('</body></html>')
	file.close()


def get_datacite_metadata(doi):
	prefix_start = doi.find('10.')
	url = 'https://api.datacite.org/works/' + doi[prefix_start:]
	print(url)
	r = requests.get(url)
	return r.json()

# Get input DOIs from excel file
df = pandas.read_excel(input_filename)
df = df.where(pandas.notnull(df), None)
data = df.to_dict()
records = []
filtered_records = []
for index in data['doi']:
	doi = data['doi'][index]
	dataset_title = data['dataset_title'][index]
	dataset_doi = data['dataset_doi'][index]
	records.append({'doi': doi, 'dataset_title': dataset_title, 'dataset_doi': dataset_doi})

prefixes = {}
publications_for_dataset = {}
dataset_dois = []
for record in records:
	publication_doi = record['doi']
	dataset_doi = record['dataset_doi']
	prefix_start = dataset_doi.find('10.')
	prefix_end = dataset_doi.find('/', prefix_start)
	prefix = dataset_doi[prefix_start:prefix_end]
	skip = False

	# De-duplicate
	if not skip:
		for filtered_record in filtered_records:
			if filtered_record['doi'] == record['doi'] and filtered_record['dataset_doi'] == record['dataset_doi']:
				skip = True
				break

	if not skip:
		filtered_records.append(record)
		dataset_dois.append(record['dataset_doi'])
		if prefix in prefixes:
			prefixes[prefix] += 1
		else:
			prefixes[prefix] = 1

		if record['dataset_doi'] not in publications_for_dataset:
			publications_for_dataset[record['dataset_doi']] = {}
		publications_for_dataset[record['dataset_doi']][record['doi']] = True
		
print('')

unique_dataset_dois = list(set(dataset_dois))
print('{0} unique dataset DOIs ({1} total)'.format(len(unique_dataset_dois), len(dataset_dois)))
print('')

for prefix in sorted(prefixes, key=prefixes.get, reverse=True):
	print(prefix, prefixes[prefix])
print('')

final_dataset_dois = []
for dataset_doi in unique_dataset_dois:
	result = get_datacite_metadata(dataset_doi)

	print('')
	if ('errors' in result):
		print('\tError ' + result['errors'][0]['status'])
	else:
		attributes = result['data']['attributes']
		title = attributes['title']
		description = attributes['description']
		published = attributes['published']
		authors = attributes['author']

		print('\ttitle:', title)
		print('\tpublished:', published)
		print('\tauthors:', len(authors))
		if (len(authors) == 0):
			print(dataset_doi)

		publications = publications_for_dataset[dataset_doi]

		if title is not None:
			render(dataset_doi, attributes, publications)
			final_dataset_doi = {}
			final_dataset_doi['doi'] = dataset_doi
			final_dataset_doi['title'] = title
			prefix_start = dataset_doi.find('10.')
			prefix_end = dataset_doi.find('/', prefix_start)
			prefix = dataset_doi[prefix_start:prefix_end]
			final_dataset_doi['prefix'] = prefix
			final_dataset_dois.append(final_dataset_doi)

	print('')


# Create the output file
print('Writing output file "{0}"'.format(output_filename))
writer = ExcelWriter(output_filename)
summary_df = pandas.DataFrame(final_dataset_dois)
summary_df.to_excel(writer, 'DOI List ({0})'.format(len(final_dataset_dois)), columns=['prefix', 'doi', 'title'])
writer.save()
print('')
