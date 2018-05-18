from nltk.parse import CoreNLPDependencyParser
from nltk.parse import CoreNLPParser
from nltk import word_tokenize
import nltk

sentences = [
    "I gave an apple to the teacher",
    "Mary missed her train to work",
    "John gave the teacher a very heavy book",
    "The sun shines"
    "This is the dog that chased the cat",
    "I saw the doctor this morning who is treating me",
    "This is the cat that the dog chased",
    "John is eager to please"
]

dep_parser = CoreNLPDependencyParser(url='http://localhost:9000')
tree_parser = CoreNLPParser(url='http://localhost:9000')

for sentence in sentences:
    parse, = dep_parser.raw_parse(sentence)
    print(parse.to_conll(10))
    print(parse.tree())

    for governor, dep, dependent in parse.triples():
        print(governor, dep, dependent)

    print("\n universal tags")
    tokens = word_tokenize(sentence)
    POS = nltk.pos_tag(tokens, tagset='universal')
    print(POS)
    print('\n')

    next(
        tree_parser.raw_parse(sentence)
    ).pretty_print()


