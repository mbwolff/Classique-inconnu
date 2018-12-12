#!/usr/bin/env python
"""
Copyright (c) 2018 Mark Wolff <wolff.mark.b@gmail.com>

Copying and distribution of this file, with or without modification, are
permitted in any medium without royalty provided the copyright notice and
this notice are preserved. This file is offered as-is, without any warranty.
"""

from __future__ import print_function
import sys
import re
import pickle
import spacy
import gensim
import os
import csv
import random
import numpy
import scipy
import itertools
import epitran
import warnings
import xml.etree.ElementTree as ET
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sourcedir = 'Fievre'
model_file = 'Fievre_model'
pkl_dict = 'pos_dict.pkl'
number_of_options = 25
no_phonemes = 3 # actually 2, the last phoneme is a space
number_of_words = 50000
positive = u'femme'
negative = u'homme'

model = gensim.models.Word2Vec.load(model_file)
pickleFile = open(pkl_dict, 'rb')
posd = pickle.load(pickleFile)
epi = epitran.Epitran('fra-Latn')
nlp = spacy.load('fr')

### BEGIN functions and classes
def delete_row_csr(mat, i):
    if not isinstance(mat, scipy.sparse.csr_matrix):
        raise ValueError("works only for CSR format -- use .tocsr() first")
    n = mat.indptr[i+1] - mat.indptr[i]
    if n > 0:
        mat.data[mat.indptr[i]:-n] = mat.data[mat.indptr[i+1]:]
        mat.data = mat.data[:-n]
        mat.indices[mat.indptr[i]:-n] = mat.indices[mat.indptr[i+1]:]
        mat.indices = mat.indices[:-n]
    mat.indptr[i:-1] = mat.indptr[i+1:]
    mat.indptr[i:] -= n
    mat.indptr = mat.indptr[:-1]
    mat._shape = (mat._shape[0]-1, mat._shape[1])

def transform_verse(assertion):
    parsed = nlp(assertion)
    new_words = []
    for word in parsed:
        try:
            hits = []
            psw = word.tag_.split('__')[0]
            for item in model.wv.most_similar(positive=[positive] + [word.lemma_.lower()], negative=[negative], topn=number_of_options):
                if posd[item[0]]:
                    psd = next(iter(posd[item[0]])).split('__')[0]
                    if (psw not in ('DET', 'PUNCT', 'ADP')) and (psw == psd):
                        hits.append(item[0])

            if len(hits) > 0:
                new_words.append(hits[0])
            else:
                new_words.append(word.text)
        except:
            new_words.append(word.text)
    response = ' '.join(new_words)
    return response

def add2corpus(corpus, string, fname, ln):
    ipa = epi.transliterate(unicode(re.sub('[\W\s]+$', ' ', string)))
    l = [fname, ln, string, ipa]
    corpus.append(l)

def readFile(fname, corpus):
    with open(os.path.join(sourcedir, fname), 'rb') as myfile:
#        string = myfile.read().decode('iso-8859-1').encode('utf8')
        string = myfile.read()
    root = ET.fromstring(string)

    node = root.find('.//SourceDesc/type')
    if node is not None and node.text == 'vers':
        string = []
        ln = 1
        for line in root.findall('.//body//l'):
            verse = unicode(line.text)
            id = int(line.attrib['id'])
            if not re.match('\w', verse):
                continue
            elif id == ln:
                string.append(verse)
            else:
                add2corpus(corpus, unicode(' '.join(string)), fname, ln)
                string = [verse]
                ln = id
        add2corpus(corpus, unicode(' '.join(string)), fname, ln)
def check_rhyme(s1,s2):
#    for l in lines:
#        l = re.sub('[\W\s]+$', '', l)
#        l = re.sub('\-', ' ', l)
#        words = l.lower().split()
#        for w in words:
#            w = re.sub('\W', '', w)
#
    if s1[-no_phonemes:] == s2[-no_phonemes:]:
        return True
    else:
        return False

def check_gender(isF,ll):
    if (isF == True and ll == u'e') or (isF == False and ll != u'e'):
        return True
    else:
        return False

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
##### END functions and classes

corpus = list()
for fname in os.listdir(sourcedir):
    if fname.endswith('xml'):
        eprint('Loading ' + fname)
        readFile(fname, corpus)

print('Un Classique inconnu\n')
print('A contribution to NaNoGenMo 2018 by Mark Wolff <wolff.mark.b@gmail.com>\n\n')
print('Positive term for word vector space analogy: ' + positive.encode('utf8'))
print('Negative term for word vector space analogy: ' + negative.encode('utf8'))
print('Number of verses in corpus: ' + str(len(corpus)))

vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    token_pattern=r'\b\w+\b',
    min_df=1)
index = random.randint(0,len(corpus))
print('Initial verse index: ' + str(index) + '\n')

vectorized_corpus = vectorizer.fit_transform([vers[2] for vers in corpus])

v_state = [] # Feminine=True, FirstVerse=True, transliteration, verse
total_words = 0
line = 0
while total_words < number_of_words:
    vers = []
    sv = corpus.pop(index)
    delete_row_csr(vectorized_corpus, index)
    tv = transform_verse(sv[2])
    vectorized_tv = vectorizer.transform([tv])
    vector_similarity = cosine_similarity(vectorized_tv, vectorized_corpus)
    got_verse = False
    if not v_state: # first verse
        index = numpy.argmax(vector_similarity)
        vers = corpus[index]
        got_verse = True
        if re.sub('[\W\s]+$', '', vers[2])[-1:] == u'e':
            v_state = [True, True, vers[3], vers[2]]
        else:
            v_state = [False, True, vers[3], vers[2]]
    else:
        topN = vector_similarity.argsort()[-number_of_options:][::-1]
        v_state_words = re.sub('[\W\s]+$', '', v_state[3]).lower().split()
        while len(topN) > 0 and got_verse == False:
            index = numpy.argmax(topN)
            topN = numpy.delete(topN, [0])
            vers = corpus[index]
            ts = re.sub('[\W\s]+$', '', vers[2])[-1:]
            vers_words = re.sub('[\W\s]+$', '', vers[2]).lower().split()
            if vers_words and vers_words[-1] != v_state_words[-1]:
                # consecutive verses cannot have the same last word
                if v_state[1] == False: # we need to complete the couplet
                    if check_rhyme(vers[3],v_state[2]) and check_gender(v_state[0],ts):
                        got_verse = True
                        v_state[2] = vers[3]
                        v_state[3] = vers[2]
                else: # start a new couplet
                    if check_gender(v_state[0],ts):
                        got_verse = True
                        v_state[2] = vers[3]
                        v_state[3] = vers[2]
    if got_verse == False:
        print('[Can\'t find a replacement verse!]')
        index = random.randint(0,len(corpus))
        v_state = []
    else:
        # print the verse
        line = line + 1
        if line % 100 == 0:
            eprint('Selected ' + str(line) + ' verses.')
        words = re.sub('[^\w\s]+', '', sv[2])
        total_words = total_words + len(words.split())
#        print(str(line) + ' ' + sv[2].encode('utf8') + '  (' + sv[0] + ':' + str(sv[1]) + ')')
        print(str(line) + ' ' + vers[2].encode('utf8') + '  (' + vers[0] + ':' + str(vers[1]) + ')')
#        print(v_state)
#        print()

        # for the next verse
        if v_state[1] == False: # next verse is first verse of couplet
            v_state[0] = not v_state[0] # next rhyme needs to switch gender
        v_state[1] = not v_state[1] # alternate between 1st and 2nd verse of couplet
