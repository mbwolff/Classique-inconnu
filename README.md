# Un classique inconnu

## A contribution to [NaNoGenMo 2018](https://github.com/NaNoGenMo/2018)

The code for this project attempts to generate a text in French with rhymed couplets of [Alexandrines](https://en.wikipedia.org/wiki/Alexandrine) using the [Théâtre Classique](http://www.theatre-classique.fr)'s online collection of French plays from the sixteenth to the nineteenth centuries.

The goal is to transform a canonical text systematically by an analogy based on a major theme in the text. By rewriting the text with other texts from the same period, it may be possible to reinvent rhetorically the text from an orthogonal perspective. Or something like that.

Here's the procedure:

1. Scrape the links for all the XML files of the plays from [this page](http://www.theatre-classique.fr/pages/programmes/PageEdition.php) and then download them to build a corpus.
2. Make a vector space for all words in the corpus using [Gensim's Word2Vec module](https://radimrehurek.com/gensim/models/word2vec.html). The words are lemmatized using [SpaCy](https://spacy.io) to simplify the vector space.
3. Build a [tf-idf matrix](https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting) for all the verses in all the plays in the corpus.
4. Choose a play in the corpus (such as Racine's [_Phèdre_](http://www.theatre-classique.fr/pages/programmes/edition.php?t=../documents/RACINE_PHEDRE.xml)) and a pair of words to form the basis of an analogy (_femme_ and _homme_, for instance). The pair will enable a modification of the play by replacing words according to the analogy (_roi_ is to _homme_ as **_reine_** is to _femme_).
5. Take the first verse in the original play and modify the verse with word substitutions based on the vector space.
6. Construct a tf-idf vector for the modified verse based on the matrix for the whole corpus.
7. Find a verse in the corpus that is most similar to the modified verse using cosine similarity. The verse must follow the pattern _aa bb cc dd ..._ where the rhymes alternate between feminine (the last word of the verse ending in a silent _e_) and masculine (the last word ending in some other letter). The [epitran module](https://github.com/dmort27/epitran) is useful for transliterating text into IPA, although it is imperfect (as its authors acknowledge) because the relationship between word spellings and phonetics in French is complicated.
8. Return to step 5, taking the next verse in the original play, and continue until every verse in the original play has been modified, vectorized, and replaced with another verse from the corpus.

Here are the first lines of the generated text:

> J'en aurais paru digne autant ou plus qu'un autre :  (CORNEILLEP_PULCHERIE.xml:994)
> Doncques vous vous plaignez d'une ingrate maîtresse ?   (DESMARETS_VISIONNAIRES.xml:1368)
> Mais un coup d'oeil peut subjuguer un sage.  (VOLTAIRE_DROITDUSEIGNEUR.xml:934)
> Qui retient mon courage  (URFE_SYLVANIRE.xml:4031)
> Mes feux, qu'ont redoublés ces propos adorables,  (CORNEILLEP_SUIVANTE.xml:913)
> Je t'ai fait un secret dont la charge m'accable ;  (NIVELLE_PREJUGEALAMODE.xml:414)
> On parle bien de vous, le Prince vous regarde   (AURE_GENEVIEVE70.xml:1357)
> Paix, voici mon vieillard.   (AURE_DIPNE.xml:315)

At the end of each verse is a reference to its source text and line number.
