import json
import numpy as np
import os
import random
import re
from decimal import Decimal
from operator import itemgetter

from constraint import *


class Parser:
    def __init__(self, path_file, constraint_definition_file="constraints-definitions.json", k=1):
        self.path_file = path_file
        self.constraint_definition_file = constraint_definition_file
        # key: word id, value: the word value
        self.words = {}

        # list of constraints
        self.constraints = []
        self.constraints_definitions = {}
        self.problem = None

        # key: word id,
        self.variables = {}
        self.joker_words = []
        self.current_joker_index = 0
        # language model
        self.bigrams = {}
        self.vocabulary = {}

        self.k = k

        # let's go !
        self.parse()
        self.modelize()

    def parse(self):
        # First, we parse the list of constraints
        print(' >>> Parsing constraints...', end='', flush=True)
        self.parse_constraints()
        print(ANSI.ok_green, 'OK !', ANSI.endc)

        # Then, we parse the definition of constraints
        print(' >>> Compiling constraints definitions...', end='', flush=True)
        self.compile_definitions()
        print(ANSI.ok_green, 'OK !', ANSI.endc)

    def parse_constraints(self):
        """
        We parse the file that contains the list of constraints we must satisfy.
        """
        input_file = open(self.path_file, "r")
        for line in input_file:
            if line != "\n":
                constraint = re.sub("[()\n]", "", line).split(" ")
                if constraint[0].lower() == "string":
                    self.words[constraint[1]] = constraint[2]
                else:
                    self.constraints.append(constraint)
        input_file.close()

    def compile_definitions(self):
        """
        We compile the JSON file that contains the definitions of the constraints.
        """
        with open(self.constraint_definition_file) as file:
            constraints_definitions = json.load(file)
            for definition in constraints_definitions["constraints"]:
                # first, we replace the field "meaning" in all the macros we have used.
                meaning = self.replace_macro(definition["meaning"], constraints_definitions["macros"])

                # Then, for each constraint in the "meaning" field of the current constraint definition,
                # we create a lambda expression representing that constraint.
                self.constraints_definitions[definition["name"]] = []
                for constraint in meaning:
                    l = "lambda " + ",".join(
                        "x" + str(i) for i in range(1, definition["#arguments"] + 1)) + ": " + constraint
                    lambda_expr = eval(l)
                    self.constraints_definitions[definition["name"]].append(lambda_expr)

            # Finally, we load the list of joker words
            # (used when trying to reduce the perplexity)
            self.joker_words = constraints_definitions["jokers"]

    def replace_macro(self, list_of_sentences, list_of_macros):
        new_list_of_sentences = []
        # if we find one macro, we replace it by the content of the macro.
        for sentence in list_of_sentences:
            current_sentence = sentence
            for macro in list_of_macros:
                if macro["name"] in sentence:
                    current_sentence = re.sub(macro["name"], str(eval(macro["meaning"])), sentence)
            new_list_of_sentences.append(current_sentence)

        return new_list_of_sentences

    def modelize(self):
        print(' >>> Modelization of the problem...', end='', flush=True)
        self.problem = Problem()
        # First, we create the variables of our LP problem
        for word, val in self.words.items():
            self.problem.addVariable(word, range(len(self.words)))

        # Then, we add the constraints
        existing_constraints = [c.lower() for c, m in self.constraints_definitions.items()]
        for contraint in self.constraints:
            unexpected_token = any([c not in self.words for c in contraint[1:]])
            if contraint[0].lower() in existing_constraints and not unexpected_token:
                for c in self.constraints_definitions[contraint[0].lower()]:
                    self.problem.addConstraint(c, [var_name for var_name in contraint[1:]])
            else:
                print(ANSI.warning, "WARNING !", ANSI.endc)
                print(ANSI.warning, ">>> Warning:", contraint, "contains token(s) that is (are) not present in the "
                                                               "constraints definition file nor in the strings. This "
                                                               "constraint is skipped.", ANSI.endc)

        # Finally, we add a constraint in order to make
        # all variable having different values
        self.problem.addConstraint(AllDifferentConstraint())
        print(ANSI.ok_green, 'OK !', ANSI.endc)

    def solve(self):
        print(' >>> Solving the problem...', end='', flush=True)
        solutions = self.problem.getSolutions()
        print(ANSI.ok_green, 'OK !', ANSI.endc)
        # if several solutions have been found,
        # we generate (or load if already exists)
        # a language model.
        if len(solutions) > 0:
            print(ANSI.bold + ANSI.ok_green + " >>>", len(solutions), "solutions found !", ANSI.endc)
            if len(solutions) > 1:
                print(" >>> Loading language model in order to rank the solutions...", end='', flush=True)
                self.generate_language_model()

            solutions_with_perplexity = []
            for solution in solutions:
                sentence = ""
                for word in sorted(solution.items(), key=itemgetter(1)):
                    sentence += self.words[word[0]] + " "
                perplexity = self.get_perplexity_from(sentence)
                solutions_with_perplexity.append((perplexity, sentence))

            solutions_with_perplexity.sort(key=itemgetter(0))
            mean_perplexity = 45
            threshold_bad_perplexity = mean_perplexity
            if solutions_with_perplexity[0][0] > 2 * threshold_bad_perplexity:
                print(ANSI.warning, "/!\ The string and ordering constraints that you entered has "
                                    "led to an utterance with a very high perplexity.", ANSI.endc)

                response = input(ANSI.bold + " >>> Do you want me to try to reduce the perplexity"
                                             " by adding one word in your sentence? (Y/n) " + ANSI.endc)

                if response.lower() == "y" or response.lower() == "yes":
                    # we try again by adding some words.
                    self.try_to_fix()
                else:
                    self.print_solution(solutions_with_perplexity[:10])
            else:
                self.print_solution(solutions_with_perplexity[:10])
        else:
            print(ANSI.fail, "/!\ No solution available. The ordering constraints that "
                             "you entered could not be satisfied.", ANSI.endc)

    @staticmethod
    def print_solution(solutions):
        print(" =============================================================")
        print(ANSI.bold, " Printing the most probable solutions based on perplexity: ", ANSI.endc)
        print(ANSI.bold + ANSI.ok_blue, " * Blue means \"Mmmh... good perplexity.\"", ANSI.endc)
        print(ANSI.warning, " * Yellow means \"Meh... Not so good.\"", ANSI.endc)
        print(ANSI.fail, " * Red means \"Uhh... I am highly perplex!", ANSI.endc)
        print(" =============================================================")
        mean_perplexity = 45
        threshold_bad_perplexity = mean_perplexity  # cf. report why 600
        for sol in solutions:
            color = ANSI.bold + ANSI.ok_blue
            if sol[0] > threshold_bad_perplexity:
                color = ANSI.ok_green
            if sol[0] > 2 * threshold_bad_perplexity:
                color = ANSI.fail
            print(color, "[ perplexity =", str(sol[0])[:5], "]", ANSI.endc, sol[1])

    def try_to_fix(self):
        # we remove the previous joker word
        if self.joker_words[self.current_joker_index] + "-$" in self.words:
            print(ANSI.ok_blue, ">>> I am going to remove the word \"",
                  self.joker_words[self.current_joker_index],
                  "\" from your sentence...", ANSI.endc)
            self.words.pop(self.joker_words[self.current_joker_index] + "-$")

        self.current_joker_index += 1
        if self.current_joker_index < len(self.joker_words):
            joker_word = self.joker_words[self.current_joker_index]
            print(ANSI.ok_blue, ">>> I am going to add the word \"", joker_word, "\" in your sentence...", ANSI.endc)
            self.words[joker_word + "-$"] = joker_word

            self.modelize()
            self.solve()
        else:
            print(ANSI.fail, "/!\ I was not be able to reduce the perplexity.", ANSI.endc)

    def generate_language_model(self, path_file="coca_bigram_lm.json"):
        """
        Generates the language model based on COCA bigram file.
        We do not regenerate it if the JSON file already exists
        :return: A language model based on the COCA bigram file.
        """
        cpt = 0
        if os.path.isfile(path_file):
            lm = json.load(open(path_file))
            self.bigrams = lm["bigrams"]
            self.vocabulary = lm["vocabulary"]
            print(ANSI.ok_green, 'OK !', ANSI.endc)
        else:
            print(ANSI.fail, 'NOT OK ! (', path_file, 'not found )', ANSI.endc)
            print(" >>> Fallback: Generating a language model based on bigrams...")
            with open("bigrams.txt") as file:
                for line in file:
                    cpt += 1
                    # bigram[0] : number of occurences
                    # bigram[1] : first word of the bigram
                    # bigram[2] : second word of the bigram
                    bigram = line.replace("\n", "").split("\t")

                    # self.vocaculary's data structure is a set.
                    # Then, insertion is in O(1) and nothing happens
                    # if item is already present in the set.
                    if bigram[1] not in self.vocabulary:
                        self.vocabulary[bigram[1]] = 0
                    if bigram[2] not in self.vocabulary:
                        self.vocabulary[bigram[2]] = 0

                    self.vocabulary[bigram[1]] += bigram[0]
                    self.vocabulary[bigram[2]] += bigram[0]

                    if bigram[1] not in self.bigrams:
                        self.bigrams[bigram[1]] = {}

                    # we create a pair <count, normalized_count>
                    # (better than having two huge matrices)
                    # normalized_count is computed in maximum_likelihood(self).
                    self.bigrams[bigram[1]][bigram[2]] = [float(bigram[0]), 0]

                    if cpt % 100000 == 0:
                        print("    >", cpt, "words processed...")

                print(" >>> All words processed!")

                print(" >>> Generating bigram probabilities...", end='', flush=True)
                self.maximum_likelihood()
                print(ANSI.ok_green, 'OK !', ANSI.endc)

                print(ANSI.bold, ">>> Exporting language model...", ANSI.endc, end='', flush=True)
                self.export()
                print(ANSI.ok_green, 'OK !', ANSI.endc)
                print(ANSI.bold, ">>> Language model successfully generated.", ANSI.endc)
                print("     Path to language model:", ANSI.ok_green, path_file, ANSI.endc)

    def maximum_likelihood(self):
        """
        Generates the likelihoods.
        """
        v = len(self.vocabulary)
        for first_word, following_word in self.bigrams.items():
            for second_word, count in following_word.items():
                probability = (following_word[second_word][0] + self.k) / (self.vocabulary[first_word] + (self.k * v))
                # recall that [first_word][second_word][0] = count
                #             [first_word][second_word][1] = normalized_count
                self.bigrams[first_word][second_word][1] = probability

    def get_perplexity_from(self, text):
        """
        Gives the perplexity of a text regarding the current language model.
        :param {string} text: the text to evaluate
        :return: The perplexity of a text according to the current language model.
        :rtype: float
        """
        txt = text.split()
        start, end = 0, 1
        p = Decimal(1.0)
        while end < len(txt):
            # If the current gram has never been encountered in the learning process
            # We compute its normalized count as (k / k*v) where k is the
            # k in add-k smoothing and v is the size of the vocabulary
            if txt[start] not in self.bigrams:
                probability = self.k / (self.k * len(self.vocabulary))
                p *= Decimal(Decimal(1.0) / Decimal(probability))
            # If the following word has never been encountered when following the first word,
            # we compute its normalized count as (k / (sum(words_count | first_word) + k*v))
            # where sum(words_count | first_word) is the number of time the second word
            # appeared right after the first word.
            elif txt[start] in self.bigrams and txt[end] not in self.bigrams[txt[start]]:
                probability = self.k / (self.vocabulary[txt[start]] + (self.k * len(self.vocabulary)))
                p *= Decimal(Decimal(1.0) / Decimal(probability))
            # the bigram is present in the language model!
            else:
                p *= Decimal(Decimal(1.0) / Decimal(self.bigrams[txt[start]][txt[end]][1]))
            start += 1
            end += 1
        res = Decimal(p ** Decimal(1 / len(txt)))
        return res

    def export(self):
        """
        Exports the current state of the model in a file.
        """
        if self.bigrams is not None:
            with open("coca_bigram_lm.json", 'w') as file:
                language_model = {
                    "bigrams": self.bigrams,
                    "vocabulary": self.vocabulary
                }
                json.dump(language_model, file, indent=4)

    def generate_random_output(self, length=300, export_to_file=True):
        """
        Generates a random output according
        to the generated language model.
        :param export_to_file: True if you want to export the result into a file.
        :param length: Length k (3 < k < 300), according to its probabilistic model
        """
        mean = []
        for i in range(1000):
            w = random.choice(list(self.vocabulary.keys()))
            text = [w]

            for j in range(15):
                while w not in self.bigrams:
                    w = random.choice(list(self.vocabulary.keys()))
                current_bigram = self.bigrams[w]
                possible_letters = [(k, v[1]) for k, v in current_bigram.items()]
                text.append(self.generate_random_from(possible_letters))
                w = text[-1]
            mu = self.get_perplexity_from(" ".join(text))
            mean.append(mu)
        print("mean perplexity: ", np.mean(mean))

    @staticmethod
    def generate_random_from(possible_letters):
        """
        Generates a random
        :parameter possible_letters: The list of (letter, corresponding proba).
        """
        # As the probabilities does not sum to 1... I think, our random will not be
        # in the range 0...1, but 0... sum{probas of the third letters for a given bigram}

        # The sort here is mandatory in order to
        # facilitate the election of the letter
        possible_letters.sort(key=itemgetter(1), reverse=True)
        r = random.uniform(0, sum([item[1] for item in possible_letters]))
        cpt = 0.0
        for item in possible_letters:
            cpt += item[1]
            if r < cpt:
                return item[0]


# Just for pretty printings
class ANSI:
    header = '\033[95m'
    ok_blue = '\033[94m'
    ok_green = '\033[92m'
    warning = '\033[93m'
    fail = '\033[91m'
    endc = '\033[0m'
    bold = '\033[1m'
    underline = '\033[4m'
