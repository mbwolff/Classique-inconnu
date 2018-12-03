# Un classique inconnu

## A contribution to [NaNoGenMo 2018](https://github.com/NaNoGenMo/2018)

The code for this project attempts to generate a text in French with rhymed couplets of [Alexandrines](https://en.wikipedia.org/wiki/Alexandrine) using the [Théâtre Classique](http://www.theatre-classique.fr)'s online collection of French plays from the sixteenth to the nineteenth centuries.

Here's the procedure:

1. Scrape the links for all the XML files of the plays from [this page](http://www.theatre-classique.fr/pages/programmes/PageEdition.php) and then download them to build a corpus.
2. Make a vector space for all words in the corpus using [Gensim's Word2Vec module](https://radimrehurek.com/gensim/models/word2vec.html). The words are lemmatized using [SpaCy](https://spacy.io) to simplify the vector space.
3. Build a [tf-idf matrix](https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting) for all the verses in all the plays in the corpus.
4. Choose a pair of words to form the basis of an analogy (_femme_ and _homme_, for instance). The pair will enable a modification of a verse by replacing words according to the analogy (_roi_ is to _homme_ as **_reine_** is to _femme_).
5. Select a random verse from the corpus and remove it from the corpus.
6. Modify the verse with word substitutions based on the vector space.
7. Construct a tf-idf vector for the modified verse based on the matrix for the whole corpus.
8. Find a verse in the corpus that is most similar to the modified verse using cosine similarity. The verse should follow the pattern _aa bb cc dd ..._ where the rhymes alternate between feminine (the last word of the verse ending in a silent _e_) and masculine (the last word ending in some other letter). The [epitran module](https://github.com/dmort27/epitran) is useful for transliterating text into IPA, although it is imperfect (as its authors acknowledge) because the relationship between word spellings and phonetics in French is complicated.
9. Return to step 6 with the selected verse and continue until the generated text contains at least 50,000 words.

Here are the first lines of the generated text:

```
1 Par ses déportements ores blanche ores brune :   (MONTCHRETIEN_CARTHAGINOISE.xml:1254)
2 Qui veut faire le mal quand il peut faire mieux.   (MONTCHRETIEN_CARTHAGINOISE.xml:1256)
3 Du jugement : mais, qu'il faut de science !  (LAFOSSEM_ECOLEDELARAISON.xml:564)
4 Si tu gardes encor la même violence,  (CORNEILLEP_VEUVE.xml:980)
5 J'afflige le meilleur, le plus tendre des pères.  (SAURIN_BLANCHEETGUISCARD.xml:618)
6 Quelles grâces vous tendre, adorable Bergère ?   (DONNEAUDEVISE_DELIE.xml:1126)
7 Le soleil en ce jour n'eût pas luit pour mes yeux.   (SAINTAIGNAN_MORTLOUISXVI.xml:646)
8 Et le dernier moment est le plus ennuyeux.  (BOURSAULT_GERMANICUS.xml:146)
9 Du moins je le souffrais en qualité d'Amant.   (CORNEILLET_INCONNU.xml:593)
10 Arrête un peu le cours de cette médisance,   (LACALPRENEDE_COMTEDESSEX.xml:1422)
11 Seigneur.  Je n'entends plus tes étranges maximes,   (LEVAYER_GRANDSELIM.xml:1399)
12 Je quitte Briseis, tu vas m'en faire un crime.  (CORNEILLET_MORTDACHILLE.xml:390)
13 Quoi ! Vous feriez cet illustre Molière,  (IMBERT_POINSINETMOLIERE.xml:1)
14 J'en parle sans humeur, vous le sentez, mon père ;  (CHABANON_FAUXNOBLE.xml:435)
```

At the end of each verse is a reference to its source text and line number.
