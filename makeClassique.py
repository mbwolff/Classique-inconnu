#!/usr/bin/env python
"""
Copyright (c) 2018 Mark Wolff <wolff.mark.b@gmail.com>

Copying and distribution of this file, with or without modification, are
permitted in any medium without royalty provided the copyright notice and
this notice are preserved. This file is offered as-is, without any warranty.
"""

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
import xml.etree.ElementTree as ET
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sourcedir = 'Fievre'
model_file = 'Fievre_model'
pkl_dict = 'pos_dict.pkl'
number_of_options = 10
original = 'RACINE_PHEDRE.xml'
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
    ipa = epi.transliterate(unicode(re.sub('\W+$', '', string)))
    l = [fname, ln, string, ipa]
    corpus.append(l)

def readFile(fname, corpus):
    with open(os.path.join(sourcedir, fname), 'rb') as myfile:
        string = myfile.read().decode('iso-8859-1').encode('utf8')
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
##### END functions and classes

corpus = list()
for fname in os.listdir(sourcedir):
    if fname.endswith('xml'):
#        print('Loading ' + fname)
        readFile(fname, corpus)

source_text = list()
readFile(original, source_text)

print('Un Classique inconnu\n')
print('A contribution to NaNoGenMo 2018 by Mark Wolff <wolff.mark.b@gmail.com>\n\n')
print('Positive term for word vector space analogy: ' + positive.encode('latin-1'))
print('Negative term for word vector space analogy: ' + negative.encode('latin-1'))
print('Number of verses in corpus: ' + str(len(corpus)))
print('Modified text: ' + original + '\n')
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    token_pattern=r'\b\w+\b',
    min_df=1)

vectorized_corpus = vectorizer.fit_transform([vers[2] for vers in corpus])

rime = [] # Feminine=True, FirstVerse=True, transliteration, verse
while len(source_text) > 0:
    sv = source_text.pop(0)
#    print('Source: ' + sv[0] + ' Line: ' + str(sv[1]) + '\n' + sv[2] + '\n')
    tv = transform_verse(sv[2])
    vectorized_tv = vectorizer.transform([tv])
    vector_similarity = cosine_similarity(vectorized_tv, vectorized_corpus)
    thisVerse = u''
    if not rime:
        i = numpy.argmax(vector_similarity)
        vers = corpus.pop(i)
        delete_row_csr(vectorized_corpus, i)
        thisVerse = vers[2]
        if vers[2][-1:] == u'e':
            rime = [True, True, vers[3], thisVerse]
        else:
            rime = [False, True, vers[3], thisVerse]
    else:
        topN = vector_similarity.argsort()[-1*number_of_options:][::-1]
        while len(topN) > 0:
            i = numpy.argmax(topN)
            topN = numpy.delete(topN, [0])
            vers = corpus[i]
            vers_words = vers[3].split()
            rime_words = rime[2].split()
#            print('Len vers_words: ' + str(len(vers_words)) + ' Len rime_words: ' + str(len(rime_words)))
            if vers_words and (vers_words[-1] != rime_words[-1]): # consecutive verses cannot have the same last word
                if rime[1] == False: # we need to complete the couplet
                    if (rime[0] == True and vers[2][-1:] == u'e' and vers[3][-2:] == rime[2][-2:]) or (vers[2][-1:] != u'e' and vers[3][-2:] == rime[2][-2:]):
                        thisVerse = vers[2]
                        corpus.pop(i)
                        delete_row_csr(vectorized_corpus, i)
                        break
                else: # start a new couplet
                    if (rime[0] == True and vers[2][-1:] == u'e') or vers[2][-1:] != u'e':
                        thisVerse = vers[2]
                        rime[2] = vers[3]
                        corpus.pop(i)
                        delete_row_csr(vectorized_corpus, i)
                        break
        if thisVerse:
            print(thisVerse.encode('latin-1') + '  (' + vers[0] + ':' + str(vers[1]) + ')')
            rime[3] = thisVerse
        else:
            print('Can\'t find a replacement verse! All done.')
            break

        rime[1] = not rime[1] # alternate between 1st and 2nd verse of couplet
        if rime[1] == True: # next verse is first verse of couplet
            rime[0] = not rime[0] # next rhyme needs to switch gender