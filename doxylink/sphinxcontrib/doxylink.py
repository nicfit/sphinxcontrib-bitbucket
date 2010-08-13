# -*- coding: utf-8 -*-
"""
See doc/index.rst for usage
"""

from docutils import nodes, utils

import os

from sphinx.util.nodes import split_explicit_title

import xml.etree.ElementTree as ET

import urlparse

import re

def find_url(doc, symbol):
	"""
	Return the URL for a given symbol.
	
	This is where the magic happens.
	This function could be a lot more clever. At present it required the passed symbol to be almost exactly the same as the entries in the Doxygen tag file.
	
	.. todo::
		
		Maybe print a list of all possible matches as a warning (but still only return the first)
	
	:Parameters:
		doc : xml.etree.ElementTree
			The XML DOM object
		symbol : string
			The symbol to lookup in the file. E.g. something like 'PolyVox::Array' or 'tidyUpMemory'
	
	:return: String representing the filename part of the URL
	"""
	
	#First check for an exact match with a top-level object (namespaces, objects etc.)
	
	#env = inliner.document.settings.env
	
	matches = []
	for compound in doc.findall('.//compound'):
		if compound.find('name').text == symbol:
			matches += [{'file':compound.find('filename').text, 'kind':compound.get('kind')}]
	
	if len(matches) > 1:
		pass
		#env.warn(env.docname, 'There were multiple matches for `%s`: %s' % (symbol, matches))
	if len(matches) == 1:
		return matches[0]
	
	
	#Strip off first namespace bit of the compound name so that 'ArraySizes' can match 'PolyVox::ArraySizes'
	for compound in doc.findall('.//compound'):
		symbol_list = compound.find('name').text.split('::', 1)
		if len(symbol_list) == 2:
			reducedsymbol = symbol_list[1]
			if reducedsymbol == symbol:
				return {'file':compound.find('filename').text, 'kind':compound.get('kind')}
	
	#Now split the symbol by '::'. Find an exact match for the first part and then a member match for the second
	#So PolyVox::Array::operator[] becomes like {namespace: "PolyVox::Array", endsymbol: "operator[]"}
	symbol_list = symbol.rsplit('::', 1)
	if len(symbol_list) == 2:
		namespace = symbol_list[0]
		endsymbol = symbol_list[1]
		for compound in doc.findall('.//compound'):
			if compound.find('name').text == namespace:
				for member in compound.findall('member'):
#					#If this compound object contains the matching member then return it
					if member.find('name').text == endsymbol:
						return {'file':(member.findtext('anchorfile') or compound.findtext('filename')) + '#' + member.find('anchor').text, 'kind':member.get('kind')}
	
	#Then we'll look at unqualified members
	for member in doc.findall('.//member'):
		if member.find('name').text == symbol:
			return {'file':(member.findtext('anchorfile') or compound.findtext('filename')) + '#' + member.find('anchor').text, 'kind':member.get('kind')}
	
	return None

def parse_tag_file(doc):
	"""
	Takes in an XML tree from a Doxygen tag file and returns a dictionary that looks something like:
	
	.. code-block:: python
	
		{'PolyVox': {'file': 'namespace_poly_vox.html',
		             'kind': 'namespace'},
		 'PolyVox::Array': {'file': 'class_poly_vox_1_1_array.html',
		                    'kind': 'class'},
		 'PolyVox::Array1DDouble': {'file': 'namespace_poly_vox.html#a7a1f5fd5c4f7fbb4258a495d707b5c13',
		                            'kind': 'typedef'},
		 'PolyVox::Array1DFloat': {'file': 'namespace_poly_vox.html#a879a120e49733eba1905c33f8a7f131b',
		                           'kind': 'typedef'},
		 'PolyVox::Array1DInt16': {'file': 'namespace_poly_vox.html#aa1463ece448c6ebed55ab429d6ae3e43',
		                           'kind': 'typedef'},
		 'QScriptContext::throwError': {'arglist': {'( Error error, const QString & text )': 'qscriptcontext.html#throwError',
		                                            '( const QString & text )': 'qscriptcontext.html#throwError-2'},
		                                'kind': 'function'},
		 'QScriptContext::toString': {'arglist': {'()': 'qscriptcontext.html#toString'},
		                              'kind': 'function'}
	
	Note the different form for functions. This is required to allow for 'overloading by argument type'.
	
	To access a filename for a symbol you do:
	
	.. code-block:: python
	
		symbol_mapping = mapping[symbol]
		if symbol_mapping['kind'] == 'function':
			url = symbol_mapping['arglist'][argument_string]
		else:
			url = symbol_mapping['file']
	
	:Parameters:
		doc : xml.etree.ElementTree
			The XML DOM object
	
	:return: a dictionary mapping fully qualified symbols to files
	"""
	mapping = {}
	for compound in doc.findall(".//compound"):
		if compound.get('kind') != 'namespace' and compound.get('kind') != 'class':
			continue #Skip everything that isn't a namespace or class
		
		#If it's a compound we can simply add it
		mapping[compound.findtext('name')] = {'kind' : compound.get('kind'), 'file' : compound.findtext('filename')}
		
		for member in compound.findall('member'):
			
			#If the member doesn't have an <anchorfile> element, use the parent compounds <filename> instead
			#This is the way it is in the qt.tag and is perhaps an artefact of old Doxygen
			anchorfile = member.findtext('anchorfile') or compound.findtext('filename')
			
			member_symbol = join(compound.findtext('name'), '::', member.findtext('name'))
			
			if member.get('kind') == 'function':
				#If we already have this function mentioned, simply append to the arglist array
				if mapping.get(member_symbol):
					mapping[member_symbol]['arglist'][member.findtext('arglist')] = join(anchorfile,'#',member.findtext('anchor'))
				else:
					mapping[member_symbol] = {'kind' : member.get('kind'), 'arglist' : {member.findtext('arglist') : join(anchorfile,'#',member.findtext('anchor'))}}
			else:
				mapping[member_symbol] = {'kind' : member.get('kind'), 'file' : join(anchorfile,'#',member.findtext('anchor'))}
	from pprint import pprint
	pprint(mapping)
	return mapping

def find_url2(mapping, symbol):
	print "\n\nSearching for", symbol
	
	#If we have an exact match then return it.
	if mapping.get(symbol):
		print ('Exact match')
		return mapping[symbol]
	
	try:
		arguments = re.search('\(.*\)', symbol).group(0) #The function arguments including the parentheses
	except AttributeError:
		arguments = ''
		
	try:
		modifiers = re.search('\s([a-zA-Z]+) ?$', symbol).group(1) #Things like 'volatile' or 'const'
	except AttributeError:
		modifiers = ''
	
	#If the user didn't pass in any arguments, i.e. `arguments == ''` then they don't care which version of the overloaded funtion they get.
	
	#First we check for any mapping entries which even slightly match the requested symbol
	#endswith_list = {}
	#for item, data in mapping.items():
	#	if item.endswith(symbol):
			#print symbol + ' : ' + item
	#		endswith_list[item] = data
	#		mapping[item]['file']
	
	#If we only find one then we return it.
	#if len(endswith_list) is 1:
	#	return endswith_list.values()[0]['file']
	
	#print("Still", len(endswith_list), 'possible matches')
	
	piecewise_list = find_url_piecewise(mapping, symbol)
	
	#If there is only one match, return it.
	if len(piecewise_list) is 1:
		return piecewise_list.values()[0]
	
	print("Still", len(piecewise_list), 'possible matches')
	
	#If there is more than one item in piecewise_list then there is an ambiguity
	#Often this is due to the symbol matching the name of the constructor as well as the class name itself
	classes_list = find_url_classes(piecewise_list, symbol)
	
	#If there is only one by here we return it.
	if len(classes_list) is 1:
		return classes_list.values()[0]
	
	print("Still", len(classes_list), 'possible matches')
	
	#If we exhaused the list by requiring classes, use the list from before the filter.
	if len(classes_list) == 0:
		classes_list = piecewise_list
	
	no_templates_list = find_url_remove_templates(classes_list, symbol)
	
	if len(no_templates_list) is 1:
		return no_templates_list.values()[0]
	
	print("Still", len(no_templates_list), 'possible matches')
	
	#If not found by now, just return the first one in the list
	if len(no_templates_list) != 0:
		return no_templates_list.values()[0]
	#Else return None if the list is empty
	else:
		return None

def find_url_piecewise(mapping, symbol):
	"""
	Match the requested symbol reverse piecewise (split on '::') against the tag names to ensure they match exactly (modulo ambiguity)
	So, if in the mapping there is "PolyVox::Volume::FloatVolume" and "PolyVox::Volume" they would be split into:
		['PolyVox', 'Volume', 'FloatVolume'] and ['PolyVox', 'Volume']
	and reversed:
		['FloatVolume', 'Volume', 'PolyVox'] and ['Volume', 'PolyVox']
	and truncated to the shorter of the two:
		['FloatVolume', 'Volume'] and ['Volume', 'PolyVox']
	If we're searching for the "PolyVox::Volume" symbol we would compare:
		['Volume', 'PolyVox'] to ['FloatVolume', 'Volume', 'PolyVox']. That doesn't match so we look at the next in the mapping:
		['Volume', 'PolyVox'] to ['Volume', 'PolyVox']. Good, so we add it to the list
	"""
	piecewise_list = {}
	for item, data in mapping.items():
		split_symbol = symbol.split('::')
		split_item = item.split('::')
		
		split_symbol.reverse()
		split_item.reverse()
		
		min_length = min(len(split_symbol), len(split_item))
		
		split_symbol = split_symbol[:min_length]
		split_item = split_item[:min_length]
		
		#print split_symbol, split_item
		
		if split_symbol == split_item:
			print symbol + ' : ' + item
			piecewise_list[item] = data
	
	return piecewise_list

def find_url_classes(mapping, symbol):
	"""Prefer classes over names of constructors"""
	classes_list = {}
	for item, data in mapping.items():
		if data['kind'] == 'class':
			print symbol + ' : ' + item
			classes_list[item] = data
	
	return classes_list

def find_url_remove_templates(mapping, symbol):
	"""Now, to disambiguate between "PolyVox::Array< 1, ElementType >::operator[]" and "PolyVox::Array::operator[]" matching "operator[]", we will ignore templated (as in C++ templates) tag names by removing names containing '<'"""
	no_templates_list = {}
	for item, data in mapping.items():
		if '<' not in item:
			print symbol + ' : ' + item
			no_templates_list[item] = data
	
	return no_templates_list

def join(*args):
	return ''.join(args)

def create_role(app, tag_filename, rootdir):
	#Tidy up the root directory path
	if not rootdir.endswith(('/', '\\')):
		rootdir = join(rootdir, os.sep)
	
	try:
		tag_file = ET.parse(tag_filename)
		mapping = parse_tag_file(tag_file)
	except (IOError):
		tag_file = None
		app.warn('Could not open tag file %s. Make sure your `doxylink` config variable is set correctly.' % tag_filename)
	
	def find_doxygen_link(name, rawtext, text, lineno, inliner, options={}, content=[]):
		text = utils.unescape(text)
		# from :name:`title <part>`
		has_explicit_title, title, part = split_explicit_title(text)
		warning_message = ''
		if tag_file:
			url = find_url(tag_file, part)
			if url:
				
				#If it's an absolute path then the link will work regardless of the document directory
				#Also check if it is a URL (i.e. it has a 'scheme' like 'http' or 'file')
				if os.path.isabs(rootdir) or urlparse.urlparse(rootdir).scheme:
					full_url = join(rootdir, url['file'])
				#But otherwise we need to add the relative path of the current document to the root source directory to the link
				else:
					relative_path_to_docsrc = os.path.relpath(app.env.srcdir, os.path.dirname(inliner.document.current_source))
					full_url = join(relative_path_to_docsrc, os.sep, rootdir, url['file'])
				
				if url['kind'] == 'function' and app.config.add_function_parentheses:
					title = join(title, '()')
				
				pnode = nodes.reference(title, title, internal=False, refuri=full_url)
				return [pnode], []
			#By here, no match was found
			warning_message = 'Could not find match for `%s` in `%s` tag file' % (part, tag_filename)
		else:
			warning_message = 'Could not find match for `%s` because tag file not found' % (part)
		
		msg = inliner.reporter.warning(warning_message, line=lineno)
		
		pnode = nodes.inline(rawsource=title, text=title)
		return [pnode], [msg]
	
	return find_doxygen_link

def setup_doxylink_roles(app):
	for name, [tag_filename, rootdir] in app.config.doxylink.iteritems():
		app.add_role(name, create_role(app, tag_filename, rootdir))

def setup(app):
	app.add_config_value('doxylink', {}, 'env')
	app.connect('builder-inited', setup_doxylink_roles)
