from conllu import parse
from TransitionBasedDependyParser import *


def conllu_to_sentence(conllu_sent):
    result = ""
    for t in conllu_sent:
        result += t["form"] + " "
    return result


if __name__ == '__main__':
    file = open("input.txt", "r")
    open("output.txt", "w").close()
    open("conftable.txt", "w").close()
    parsed_file = parse(file.read())
    cpt = 1
    for conllu_sentence in parsed_file:
        text = conllu_to_sentence(conllu_sentence)
        parser = TransitionBasedDependencyParser(conllu_sentence, cpt, text)
        parser.parse()
        print("sentence", cpt, "done")
        cpt += 1
