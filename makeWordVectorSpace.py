#!/usr/bin/env python
"""
Copyright (c) 2018 Mark Wolff <wolff.mark.b@gmail.com>

Copying and distribution of this file, with or without modification, are
permitted in any medium without royalty provided the copyright notice and
this notice are preserved. This file is offered as-is, without any warranty.
"""

import os
import pickle
import spacy
import re
import csv
import logging
import gensim
import shutil
import xml.etree.ElementTree as ET
from six import iteritems

sourcedir = 'Fievre'

pickledir = 'Fievre_pickled'
saved = re.sub('pickled$', 'model', pickledir)
pos_dict = 'pos_dict.pkl'

### functions and classes
def getTagged(path):
	pickleFile = open(path, 'rb')
	sentences = pickle.load(pickleFile)
	return sentences

class MySentences(object):
	def __init__(self, dirname):
		self.dirname = dirname
	def __iter__(self):
		for fname in os.listdir(self.dirname):
			if fname.endswith('pkl'):
				for sent in getTagged(os.path.join(self.dirname, fname)):
					yield sent

nlp = spacy.load('fr')

if not os.path.exists(pickledir):
    os.makedirs(pickledir)

pd = dict()
num_files = 0
for fname in os.listdir(sourcedir):
    if fname.endswith('xml'):
#		print(fname)
		nfname = re.sub('xml$', 'pkl', fname)
		if os.path.exists(os.path.join(pickledir, nfname)):
			print('Already have ' + nfname)
			continue
		with open(os.path.join(sourcedir, fname), 'rb') as myfile:
			string = myfile.read().decode('iso-8859-1').encode('utf8')
		try:
			root = ET.fromstring(string)
		except:
			continue

		node = root.find('.//SourceDesc/type')
		if node is not None and node.text == 'vers':
#		if root.find('.//SourceDesc/type').text == 'vers':
			num_files = num_files + 1
			print(str(num_files) + ' ' + fname)
			string = unicode()
			work = list()
			ln = 1
			for line in root.findall('.//body//l'):
				verse = unicode(line.text)
				id = int(line.attrib['id'])
#				print(str(id))
				if id == ln:
					string = string + u' ' + verse
				else:
					work.append(re.sub('^\s+', '', string))
					string = verse
					ln = id
			work.append(re.sub('^\s+', '', string))
	        sections = []
	        current_section = ''
	        last_chunk = work.pop()
	        for chunk in work:
	            if len(current_section) + len(chunk) + 1 < 1000000:
				# Spacy requires texts of length no more than 1000000
	                current_section = current_section + ' ' + chunk
	            else:
	                sections.append(current_section)
	                current_section = chunk

	        current_section = current_section + last_chunk
	        sections.append(re.sub('^\s+', '', current_section))

	        section_counter = 0
	        for section in sections:
	            doc = nlp(unicode(section))
	            parsed = [(w.text, w.tag_, w.lemma_) for w in doc]

	            sentences = []
	            sent = []
	            for token in parsed:
	                text = token[0]
	                pos = token[1]
	                lemma = token[2].lower()

	                if re.match('PUNCT', pos) and re.match(r'[\.\!\?]', text):
	                    sent.append(lemma)
	                    sentences.append(sent)
	                    sent = []

	                else:
	                    if not re.match('PUNCT', pos):
	                        lemma = re.sub('^\W+', '', lemma)
	                        lemma = re.sub('\W+$', '', lemma)

	                    if re.match('\w', pos):
	                        sent.append(lemma)
	                        if pd.get(lemma): pd[lemma] = pd.get(lemma).add(pos)
	                        else: pd[lemma] = { pos }

	            if len(sent) > 0: sentences.append(sent)
	            fn = nfname
	            if len(sections) > 1:
	                fn = re.sub('pkl$', str(section_counter) + '.pkl', fn)
	                section_counter = section_counter + 1

				# print(os.path.join(pickledir, fn))
	            pickleFile = open(os.path.join(pickledir, fn), 'wb')
	            pickle.dump(sentences, pickleFile)

pickleFile = open(pos_dict, 'wb')
pickle.dump(pd, pickleFile)

sentences = MySentences(pickledir) # a memory-friendly iterator
model = gensim.models.Word2Vec(sentences, workers=4)
model.init_sims(replace=True)
model.save(saved)

shutil.rmtree(pickledir)
