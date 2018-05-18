from Oracle import Oracle


class TransitionBasedDependencyParser:
    def __init__(self, conllu_sentence, id_sentence, sentence):
        self.iteration = 0
        self.input_buffer = list()
        for t in conllu_sentence:
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
            self.parse_trace += str(self.iteration) + "\t[" + ",".join(str(x) for x in self.stack) + "]\t[" + ",".join(str(x) for x in self.input_buffer)
            self.parse_trace += "]\tLEFTARC\t(" + str(head) + "<-" + str(dependent) + ")\n"
        elif action == "rightarc":
            self.parse_trace += str(self.iteration) + "\t[" + ",".join(str(x) for x in self.stack) + "]\t[" + ",".join(str(x) for x in self.input_buffer)
            self.parse_trace += "]\tRIGHTARC\t(" + str(head) + "->" + str(dependent) + ")\n"
        elif action == "shift":
            self.parse_trace += str(self.iteration) + "\t[" + ",".join(str(x) for x in self.stack) + "]\t[" + ",".join(str(x) for x in self.input_buffer)
            self.parse_trace += "]\tSHIFT\n"

    def apply(self, transition_operator):
        assert transition_operator in ["shift", "leftarc", "rightarc", "done"]

        if transition_operator == "shift":
            self.shift()
        elif transition_operator == "leftarc":
            self.left_arc()
        else:
            self.right_arc()

    def export_trace(self):
        self.parse_trace += str(self.iteration) + "\t[root]\t[]\tDone\n</sentence>\n\n"
        file = open("trace_sentences.txt", "a")
        file.write(self.parse_trace)
        file.close()

    def export_conllu(self):
        file = open("conllu_sentences.txt", "a")
        file.write("# sent_id = " + str(self.id_sentence) + "\n# text = " + self.sentence + "\n")
        file.write("#1.ID\t2.FORM\t3.LEMMA\t4.UPOSTAG\t5.XPOSTAG\t6.FEATS\t7.HEAD\t8.DEPREL\n")
        for token in self.original_conllu_sentence:
            file.write(str(token.id) + "\t" + token.form + "\t" + token.lemma + "\t" + token.upostag
                       + "\t_\t_\t" + str(self.dependency_relations[token.id]) + "\tDEP\n")
        file.write("\n\n")
        file.close()


class ConLLUToken:
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
