#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

Python IcyMeta class:
	get icy-meta from audio stream (content-type, bitrate, genre, name...)

Idea:
	http://anton.logvinenko.name/en/blog/how-to-get-title-from-audio-stream-with-python.html

@author       fffilo
@link         -
@github       -
@version      0.0.1
@license      -

'''

### Import modules
import os, urllib2, re, time

# module info
__author__ = 'fffilo'
__version__ = '0.0.1'
__path__ = os.path.realpath(__file__)

### IcyMeta Class
class IcyMeta:

	# urllib2 request timeout
	__timeout = 2

	# request url
	__url = None

	# contructor
	def __init__(self, url):
		self.__url = url
		self.refresh()

	# destructor
	def __del__(self):
		pass

	# get header value for key
	def __read_header(self, key):
		regex = re.compile('(^|\n|\r)(' + key.replace('-', '\\-') + ')(\:\s?)([^\n|^\r|^$]*)(\n|\r|$)', flags=re.IGNORECASE)
		match = re.search(regex, self.__headers)
		result = None

		if match is not None and len(match.groups()) == 5:
			result = match.group(4)

		return result

	# get headers (metadata)
	def __fix_header(self, response):
		if self.__headers.strip() == '':
			# read headers from response
			self.__headers = ''
			line = response.readline()

			# header is in content
			if line.strip() == 'ICY 200 OK':
				while line != '\r\n':
					self.__headers += line
					line = response.readline()

	# get content (song title with some byte shift)
	def __fix_content(self, response):
		metaint = self.__read_header('icy-metaint')
		if metaint is None:
			return

		metaint = int(metaint)
		read_buffer = metaint + 255

		self.__content = response.read(read_buffer)
		self.__content = self.__content[metaint:]

	# clean private variables
	def __clean(self):
		self.__headers = ''
		self.__content = ''
		self.__error = None
		self.__status = None
		self.__timestamp = None

	# execute urlopen (get headers/content)
	def __request(self):
		request = urllib2.Request(self.__url)
		request.add_header('Icy-MetaData', 1)

		try:
			response = urllib2.urlopen(request, timeout=self.__timeout)

			self.__timestamp = time.time()
			self.__status = response.getcode()
			self.__headers = str(response.headers)

			self.__fix_header(response)
			self.__fix_content(response)

			response.close()
		except Exception, e:
			self.__error = str(e)

	# execute request
	def refresh(self):
		self.__clean()
		self.__request()

	# get request error
	def error(self):
		return self.__error

	# get request status code
	def status(self):
		return self.__status

	# get request timestamp
	def timestamp(self):
		return self.__timestamp

	# get metadata from headers/content
	def metadata(self):
		result = {}

		# get each metadata from header
		for meta in ['icy-br', 'icy-genre', 'icy-name', 'icy-notice1', 'icy-notice2', 'icy-pub', 'icy-url', 'content-type']:
			attr = meta.replace('icy-', '')
			result[attr] = self.__read_header(meta)

			# convert br|pub to integer
			if (result[attr] is not None) and (meta == 'icy-br' or meta == 'icy-pub'):
				try:
					result[attr] = int(result[attr])
				except Exception, e:
					pass

		# song title is inside content
		result['title'] = None
		if self.__content.strip() != '':
			#result['title'] = self.__content.split("'")[1].strip()

			regex = re.compile('(Title=\')(.*)(\';Stream)', flags=re.IGNORECASE)
			match = re.search(regex, self.__content)
			if match is not None:
				result['title'] = match.group(2).strip()

		return result

### Icy-metadata CLI
if __name__ == '__main__':
	import sys

	# arguments
	_format = 'plain'
	_prettify = False
	_url = None

	# display error
	def __error(errstr, errnum):
		print 'E: ' + errstr
		exit(errnum);

	# display help
	def __help():
		exe = os.path.realpath(sys.argv[0])
		if not os.access(exe, os.X_OK):
			exe = 'python ' + exe
		if os.path.isfile('/usr/bin/icymeta') and os.path.realpath('/usr/bin/icymeta') == os.path.realpath(__file__):
			exe = '/usr/bin/icymeta'

		print 'Displays icy-metadata of audio stream.'
		print ''
		print 'Usage:'
		print '  ' + exe + ' --url={url} [--format={format}] [--prettify]'
		print ''
		print 'Options:'
		print '  --url       Audio stream URL'
		print '  --format    Output format (plain|json|csv|xml)'
		print '  --prettify  Prettifies output format'
		print '  --help      This help text'

		exit(0)

	# get arguments
	def __args():
		global _format, _url, _prettify

		if len(sys.argv) <= 1:
			__help()

		for argv in sys.argv[1:]:
			if argv == '--help':
				__help()
			elif argv == '--help=':
				__error('Wrong use of --help argument.', 1002)
			elif argv == '--url' or argv == '--url=':
				__error('Wrong use of --url argument.', 1003)
			elif argv[:6] == '--url=':
				_url = argv[6:]
			elif argv[:11] == '--prettify=':
				__error('Wrong use of --prettify argument.', 1004)
			elif argv[:10] == '--prettify':
				_prettify = True
			elif argv == '--format' or argv == '--format=':
				__error('Wrong use of --format argument.', 1005)
			elif argv[:9] == '--format=':
				_format = argv[9:]
			else:
				__error('Unknown argument ' + argv + '.', 1001)

		if _format.lower() != 'plain' and _format.lower() != 'json' and _format.lower() != 'csv' and _format.lower() != 'xml':
			__error('Unknown format ' + _format + '.', 1006)

	# execute icymeta
	def __exec():
		icy = IcyMeta(_url)

		data = {}
		data['metadata'] = icy.metadata()
		data['status'] = icy.status()
		data['error'] = icy.error()
		data['timestamp'] = icy.timestamp()

		if _format == 'json':
			__json(data, _prettify)
		elif _format == 'csv':
			__csv(data, _prettify)
		elif _format == 'xml':
			__xml(data, _prettify)
		else:
			__plain(data, _prettify)

	# display icymeta as plain text
	def __plain(data, prettify):
		print 'status: ' + ('               ' if prettify else '') + ('' if data['status'] is None else str(data['status']))
		print 'error: ' + ('                ' if prettify else '') + ('' if data['error'] is None else str(data['error']))
		print 'timestamp: ' + ('            ' if prettify else '') + ('' if data['timestamp'] is None else str(data['timestamp']))
		print 'metadata.br: ' + ('          ' if prettify else '') + ('' if data['metadata']['br'] is None else str(data['metadata']['br']))
		print 'metadata.genre: ' + ('       ' if prettify else '') + ('' if data['metadata']['genre'] is None else str(data['metadata']['genre']))
		print 'metadata.name: ' + ('        ' if prettify else '') + ('' if data['metadata']['name'] is None else str(data['metadata']['name']))
		print 'metadata.title: ' + ('       ' if prettify else '') + ('' if data['metadata']['title'] is None else str(data['metadata']['title']))
		print 'metadata.notice1: ' + ('     ' if prettify else '') + ('' if data['metadata']['notice1'] is None else str(data['metadata']['notice1']))
		print 'metadata.notice2: ' + ('     ' if prettify else '') + ('' if data['metadata']['notice2'] is None else str(data['metadata']['notice2']))
		print 'metadata.pub: ' + ('         ' if prettify else '') + ('' if data['metadata']['pub'] is None else str(data['metadata']['pub']))
		print 'metadata.url: ' + ('         ' if prettify else '') + ('' if data['metadata']['url'] is None else str(data['metadata']['url']))
		print 'metadata.content-type: ' + ('' if prettify else '') + ('' if data['metadata']['content-type'] is None else str(data['metadata']['content-type']))

	# display icymeta as json
	def __json(data, prettify):
		import json
		if prettify:
			print json.dumps(data, default=lambda o: o.__dict__, indent=4)
		else:
			print json.dumps(data)

	# display icymeta as csv
	def __csv(data, prettify):
		print '"status";"error";"timestamp";"metadata.br";"metadata.genre";"metadata.name";"metadata.title";"metadata.notice1";"metadata.notice2";"metadata.pub";"metadata.url";"metadata.content-type";'
		print '"' + ('' if data['status'] is None else str(data['status']).replace('"', '\\"')) + '"' + ';' + '"' + ('' if data['error'] is None else str(data['error']).replace('"', '\\"')) + '"' + ';' + '"' + ('' if data['timestamp'] is None else str(data['timestamp']).replace('"', '\\"')) + '"' + ';' + '"' + ('' if data['metadata']['br'] is None else str(data['metadata']['br']).replace('"', '\\"')) + '"' + ';' + '"' + ('' if data['metadata']['genre'] is None else str(data['metadata']['genre']).replace('"', '\\"')) + '"' + ';' + '"' + ('' if data['metadata']['name'] is None else str(data['metadata']['name']).replace('"', '\\"')) + '"' + ';' + '"' + ('' if data['metadata']['title'] is None else str(data['metadata']['title']).replace('"', '\\"')) + '"' + ';' + '"' + ('' if data['metadata']['notice1'] is None else str(data['metadata']['notice1']).replace('"', '\\"')) + '"' + ';' + '"' + ('' if data['metadata']['notice2'] is None else str(data['metadata']['notice2']).replace('"', '\\"')) + '"' + ';' + '"' + ('' if data['metadata']['pub'] is None else str(data['metadata']['pub']).replace('"', '\\"')) + '"' + ';' + '"' + ('' if data['metadata']['url'] is None else str(data['metadata']['url']).replace('"', '\\"')) + '"' + ';' + '"' + ('' if data['metadata']['content-type'] is None else str(data['metadata']['content-type']).replace('"', '\\"')) + '"' + ';'

	# display icymeta as xml
	def __xml(data, prettify):
		from lxml import etree
		docroot = etree.Element('doc')
		child = etree.Element('status')
		child.text = '' if data['status'] is None else str(data['status'])
		docroot.append(child)
		child = etree.Element('error')
		child.text = '' if data['error'] is None else str(data['error'])
		docroot.append(child)
		child = etree.Element('timestamp')
		child.text = '' if data['timestamp'] is None else str(data['timestamp'])
		docroot.append(child)
		child = etree.Element('metadata')
		docroot.append(child)
		sub = etree.Element('br')
		sub.text = '' if data['metadata']['br'] is None else str(data['metadata']['br'])
		child.append(sub)
		sub = etree.Element('genre')
		sub.text = '' if data['metadata']['genre'] is None else str(data['metadata']['genre'])
		child.append(sub)
		sub = etree.Element('genre')
		sub.text = '' if data['metadata']['genre'] is None else str(data['metadata']['genre'])
		child.append(sub)
		sub = etree.Element('title')
		sub.text = '' if data['metadata']['title'] is None else str(data['metadata']['title'])
		child.append(sub)
		sub = etree.Element('notice1')
		sub.text = '' if data['metadata']['notice1'] is None else str(data['metadata']['notice1'])
		child.append(sub)
		sub = etree.Element('notice2')
		sub.text = '' if data['metadata']['notice2'] is None else str(data['metadata']['notice2'])
		child.append(sub)
		sub = etree.Element('pub')
		sub.text = '' if data['metadata']['pub'] is None else str(data['metadata']['pub'])
		child.append(sub)
		sub = etree.Element('url')
		sub.text = '' if data['metadata']['url'] is None else str(data['metadata']['url'])
		child.append(sub)
		sub = etree.Element('content-type')
		sub.text = '' if data['metadata']['content-type'] is None else str(data['metadata']['content-type'])
		child.append(sub)
		print etree.tostring(docroot, encoding='UTF-8', xml_declaration=True, pretty_print=prettify)

	# go, go go...
	__args()
	__exec()

	exit()
