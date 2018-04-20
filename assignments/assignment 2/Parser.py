from conllu import parse


class Oracle:
    def __init__(self):
        """
        Creates an instance of an oracle.
        """
        self.reference_parse = {}

    def set_reference_set(self, reference_parse):
        """
        set the set of features
        :param reference_parse: path to the file containing the features.
        """
        file = open(reference_parse, "r")
        for line in file.readlines():
            l = line.split(",")
            config = l[:2] if len(l) == 3 else l[:1]
            action = l[-1].replace(" ", "").replace("\n", "").replace("op=", "").lower()
            self.reference_parse["".join(config)] = action

    def consult(self, stack, input_buffer):
        """
        Consults the oracle.
        :param stack: the stack
        :param input_buffer: the input buffer
        :return: the 'correct' choice according to the Oracle.
        """
        # we check for s1+b1
        action = ""
        if len(stack) > 0:
            feature = "s1.t=" + stack[-1].upostag.lower() + " "
            if len(stack) > 1 and stack[-1].upostag.lower() == 'det' and len(input_buffer) > 0:
                action = "shift"
            elif len(stack) > 1 and ((stack[-1].upostag.lower() == 'verb' and len(input_buffer) == 0)
                                     or stack[-1].upostag.lower() != 'verb'):
                # but first, if this a verb and the previous is
                # the root, then we shouldn't go further
                feature += "s2.t=" + stack[-2].upostag.lower()
                if feature in self.reference_parse:
                    action = self.reference_parse[feature]
                # we check for s1,b1
                elif len(input_buffer) > 0:
                    feature = "s1.t=" + stack[-1].upostag.lower() + " "
                    feature += "b1.t=" + input_buffer[0].upostag.lower()

                    # we check if s1,b1 exists in the reference parse
                    if feature in self.reference_parse:
                        action = self.reference_parse[feature]

                    # did not work, we only check for s
                    else:
                        feature = "s1.t=" + stack[-1].upostag.lower() + " "

                        if feature in self.reference_parse:
                            action = self.reference_parse[feature]
                        # Uuuh... ?!
                        else:
                            raise ValueError("Incoherrent state: ", feature)

            # we check for s1,b1
            elif len(input_buffer) > 0:
                feature = "s1.t=" + stack[-1].upostag.lower() + " "
                feature += "b1.t=" + input_buffer[0].upostag.lower()

                # we check if s1,b1 exists in the reference parse
                if feature in self.reference_parse:
                    action = self.reference_parse[feature]

                # did not work, we only check for s
                else:
                    feature = "s1.t=" + stack[-1].upostag.lower() + " "

                    if feature in self.reference_parse:
                        action = self.reference_parse[feature]
                    # Uuuh... ?!
                    else:
                        raise ValueError("Incoherrent state: ", feature)

        return action


class TransitionBasedDependencyParser:
    def __init__(self, conllu_s, id_sentence, sentence):
        self.iteration = 0
        self.input_buffer = list()
        for t in conllu_s:
            # t is an ordered dictionnary [("id", <val>), ("form", <val>), ("lemma", <val>), ("upostag", <val>)]
            self.input_buffer.append(ConLLUToken(t["id"], t["form"], t["lemma"], t["upostag"]))

        self.original_conllu_sentence = list(self.input_buffer)
        self.sentence = sentence
        self.stack = list()
        self.dependency_relations = {}
        self.token_id = 0
        self.oracle = Oracle()
        self.oracle.set_reference_set("feattemp.txt")
        self.parse_trace = '<sentence file="input.txt" id="' + str(id_sentence) + ' text="' + sentence + '">\n'
        self.parse_trace += "Step\tStack\tWord List\tAction\tRelationAdded\n"
        self.id_sentence = id_sentence

    def parse(self):
        # Initial state
        # input buffer already set in the constructor
        self.stack.append(ConLLUToken.create_root_token())
        while not self.is_done():
            transition_operator = self.oracle.consult(self.stack, self.input_buffer)
            self.apply(transition_operator)

        self.export_trace()
        self.export_conllu()

    def is_done(self):
        assert len(self.stack) > 0
        return len(self.input_buffer) == 0 and self.stack[-1].is_root()

    def shift(self):
        # self.add_to_trace(Action.SHIFT.name)
        assert len(self.input_buffer) > 0
        self.update_trace("shift", None, None)
        element = self.input_buffer.pop(0)
        self.stack.append(element)

    def left_arc(self):
        assert len(self.stack) > 1 and not self.stack[-2].is_root()
        self.update_trace("leftarc", self.stack[-1], self.stack[-2])
        head = self.stack[-1]
        dependent = self.stack.pop(-2)
        self.dependency_relations[dependent.id] = head.id

    def right_arc(self):
        assert len(self.stack) > 1
        self.update_trace("rightarc", self.stack[-1], self.stack[-2])
        if self.stack[-2].is_root():
            self.dependency_relations[self.stack[-1].id] = 0
        else:
            self.dependency_relations[self.stack[-1].id] = self.stack[-2].id
        self.stack.pop()

    def update_trace(self, action, head, dependent):
        self.iteration += 1
        if action == "leftarc":
            self.parse_trace += str(self.iteration) + "\t[" + ",".join(str(x) for x in self.stack) + "]\t[" + ",".join(
                str(x) for x in self.input_buffer)
            self.parse_trace += "]\tLEFTARC\t(" + str(head) + "<-" + str(dependent) + ")\n"
        elif action == "rightarc":
            self.parse_trace += str(self.iteration) + "\t[" + ",".join(str(x) for x in self.stack) + "]\t[" + ",".join(
                str(x) for x in self.input_buffer)
            self.parse_trace += "]\tRIGHTARC\t(" + str(head) + "->" + str(dependent) + ")\n"
        elif action == "shift":
            self.parse_trace += str(self.iteration) + "\t[" + ",".join(str(x) for x in self.stack) + "]\t[" + ",".join(
                str(x) for x in self.input_buffer)
            self.parse_trace += "]\tSHIFT\n"

    def apply(self, transition_operator):
        """
        this function is called just after we consult the oracle.
        :param transition_operator: the operation to apply
        """
        assert transition_operator in ["shift", "leftarc", "rightarc", "done"]

        if transition_operator == "shift":
            self.shift()
        elif transition_operator == "leftarc":
            self.left_arc()
        else:
            self.right_arc()

    def export_trace(self):
        """
        exports the trace configuration of the parsing.
        """
        self.parse_trace += str(self.iteration) + "\t[root]\t[]\tDone\n</sentence>\n\n"
        f = open("conftable.txt", "a")
        f.write(self.parse_trace)
        f.close()

    def export_conllu(self):
        f = open("output.txt", "a")
        f.write("# sent_id = " + str(self.id_sentence) + "\n# text = " + self.sentence + "\n")
        f.write("#1.ID\t2.FORM\t3.LEMMA\t4.UPOSTAG\t5.XPOSTAG\t6.FEATS\t7.HEAD\t8.DEPREL\n")
        for token in self.original_conllu_sentence:
            f.write(str(token.id) + "\t" + token.form + "\t" + token.lemma + "\t" + token.upostag
                       + "\t_\t_\t" + str(self.dependency_relations[token.id]) + "\tDEP\n")
        f.write("\n\n")
        f.close()


class ConLLUToken:
    """
    Simple wrapper for a conllu word.
    """
    def __init__(self, identifier, form, lemma, upostag):
        self.id = identifier
        self.form = form
        self.lemma = lemma
        self.upostag = upostag
        self.head = "_"
        self.deprel = "_"

    def is_root(self):
        return self.upostag == "root"

    def __str__(self):
        return self.form

    @staticmethod
    def create_root_token():
        return ConLLUToken(0, "root", "root", "root")


def conllu_to_sentence(conllu_sent):
    result = ""
    for t in conllu_sent:
        result += t["form"] + " "
    return result

"""
Python-like main function
"""
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
