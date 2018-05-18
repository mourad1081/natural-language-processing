class Oracle:
    def __init__(self):
        self.reference_parse = {}

    def set_reference_set(self, reference_parse):
        file = open(reference_parse, "r")
        for line in file.readlines():
            l = line.split(",")
            config = l[:2] if len(l) == 3 else l[:1]
            action = l[-1].replace(" ", "").replace("\n", "").replace("op=", "").lower()
            self.reference_parse["".join(config)] = action

    def consult(self, stack, input_buffer):
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
