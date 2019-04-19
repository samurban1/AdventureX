from nltk.corpus import stopwords
from nltk import word_tokenize, pos_tag
# from nltk.stem import wordnet, WordNetLemmatizer


def add_the(tokenized):
    """Adds a 'the' before a noun to make the POS tagger more accurate."""
    print('tokenized before the:', tokenized, type(tokenized))
    objects = ''
    for references in [item.references for item in OBJECTS.values()]:
        objects += ' '.join(references) + ' '
    print(objects)
    for word in tokenized:
        if word in objects:
            if tokenized[tokenized.index(word)-1] != 'the':  # if there is not already a "the" before the word
                first = tokenized[:tokenized.index(word)]
                last = tokenized[tokenized.index(word):]
                tokenized = first + ['the'] + last
    # print('tokenized after the:', tokenized)
    return tokenized

def process_content(text):
    """Tokenizes text, adds 'the' in front of nouns to make POS tagger more accurate, and then spits out
    a list of tuples, whose values are the word and then the part of speech."""
    tokenized = word_tokenize(text)  # tokenizes words and then adds 'the' in front of nouns using add_the func
    filtered = [word for word in tokenized if word in needed or word not in unNeeded]

    try:
        tagged = pos_tag(tokenized)
        print(tagged, type(tagged))
        print('tagged:', tagged)
        final = [(word, tag) for word, tag in tagged if word in filtered]
        print(final)

    except Exception as e:
        print(Exception, str(e))


keywords = ['None', 'and', 'else', 'except', 'finally', 'for', 'from', 'if', 'import', 'in', 'is', 'not', 'or', 'with']

unNeeded = list(stopwords.words('english'))
needed = ['in']

while True:
    ex_text = input('Input commmand: ')
    if 'exit' in ex_text:
        break
    process_content(ex_text)

#
# # lemmatization
# word_lem = WordNetLemmatizer()
# word_lem.lemmatize('giving')
# punctuation = re.compile(r'[-.?!,:;()|0-9]')
# no_punct = []
# for words in ['i', 'went', 'to', 'the', 'store', '.', 'and', ':', ':?l', 'then,', 'i', 'went', 'home', '?']:
#     word = punctuation.sub('', words)
#     if len(word) > 0:
#         no_punct.append(word)
# learn chunking in nltk

pos_list = """
CC coordinating conjunction
CD cardinal digit
DT determiner
EX existential there (like: “there is” … think of it like “there exists”)
FW foreign word
IN preposition/subordinating conjunction
JJ adjective ‘big’
JJR adjective, comparative ‘bigger’
JJS adjective, superlative ‘biggest’
LS list marker 1)
MD modal could, will
NN noun, singular ‘desk’
NNS noun plural ‘desks’
NNP proper noun, singular ‘Harrison’
NNPS proper noun, plural ‘Americans’
PDT predeterminer ‘all the kids’
POS possessive ending parent’s
PRP personal pronoun I, he, she
PRP$ possessive pronoun my, his, hers
RB adverb very, silently,
RBR adverb, comparative better
RBS adverb, superlative best
RP particle give up
TO, to go ‘to’ the store.
UH interjection, errrrrrrrm
VB verb, base form take
VBD verb, past tense took
VBG verb, gerund/present participle taking
VBN verb, past participle taken
VBP verb, sing. present, non-3d take
VBZ verb, 3rd person sing. present takes
WDT wh-determiner which
WP wh-pronoun who, what
WP$ possessive wh-pronoun whose
WRB wh-abverb where, when
"""
