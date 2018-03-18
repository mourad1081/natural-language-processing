import os
import random
import re as regexp
import json
from operator import itemgetter

from math import log


class LanguageModel:

    def __init__(self, path_file):
        """
        Creates an object that can modelize a language
        given the path to a corpus.
        :param path_file Path to the file to process.
        """
        self.path_file = path_file
        file = open(path_file, "r", encoding="utf-8")
        self.text = "".join(file.readlines())
        self.name = os.path.basename(path_file)
        self.vocabulary = None
        self.trigrams_count = None
        self.trigrams_normalized = None
        self.k_smoothed = False
        self.k = 0
        self.clean()
        self.generate_vocabulary()

        file.close()

    def clean(self):
        """
        Cleans the text without modifying the input file.
        The function transforms all non-char characters
        to double underscores.
        """
        print(' ➤➤➤ Cleaning text...', end='', flush=True)
        self.text = regexp.sub(" ", "__", self.text.lower(), flags=regexp.MULTILINE)
        self.text = "_" + regexp.sub("[^_a-zA-Z]", "", self.text, flags=regexp.MULTILINE) + "_"
        print(ANSI.ok_green, 'OK ✓', ANSI.endc)

    def export(self):
        """
        Exports the current state of the text in a file.
        """
        if self.trigrams_normalized is not None:
            with open(self.path_file + "__language_model.json", 'w') as file:
                json.dump(self.trigrams_normalized, file, indent=4)
            print(ANSI.bold, "➤➤➤ Language model successfully generated.", ANSI.endc)
            print("     Path to language model: ", ANSI.ok_green, self.path_file + "__language_model.json", ANSI.endc)

    def generate_vocabulary(self):
        """
        Generates the vocabulary of the text.
        """
        print(' ➤➤➤ Generating vocabulary...', end='', flush=True)
        self.vocabulary = {}
        for letter in self.text:
            if letter in self.vocabulary.keys():
                self.vocabulary[letter] += 1
            else:
                self.vocabulary[letter] = 1

        print(ANSI.ok_green, 'OK ✓', ANSI.endc)

    def generate_trigrams_counts(self):
        """
        Counts all letter 3-grams
        """
        print(' ➤➤➤ Generating trigram counts...', end='', flush=True)
        # We create a 2D matrix : column = P(w_i | w_i-2, w_i-1)
        self.trigrams_count = self.generate_all_trigrams()
        start, offset_bigram, i = 0, 2, 2

        while i < len(self.text):
            preceding_bigram = self.text[start:offset_bigram]
            current_letter = self.text[i]

            self.trigrams_count[preceding_bigram][current_letter] += 1

            start += 1
            offset_bigram += 1
            i += 1
        print(ANSI.ok_green, 'OK ✓', ANSI.endc)

    def normalize_counts(self):
        """
        Transform the matrix to a language model.
        """
        print(' ➤➤➤ Generating trigram probabilities...', end='', flush=True)
        self.trigrams_normalized = self.generate_all_trigrams()
        v = len(self.vocabulary)
        for bigram, following_letters in self.trigrams_count.items():
            for letter, count in following_letters.items():
                denominator = sum([v for k, v in following_letters.items()])
                if self.k_smoothed:
                    probability = following_letters[letter] / (denominator + (self.k * v))
                else:
                    probability = following_letters[letter] / denominator

                self.trigrams_normalized[bigram][letter] = probability
        print(ANSI.ok_green, 'OK ✓', ANSI.endc)

    def percentage_of_zeros(self):
        """
        Returns the percentage of zeros in the matrix.
        :return: The percentage (between 0 and 100).
        """
        if self.k_smoothed:
            print(ANSI.warning,
                  "➤➤➤ WARNING: As you already smoothed the counts, there will probably be 0 zeros.",
                  ANSI.endc)

        zeros, non_zeros = 0, 0
        for bigram, following_letter in self.trigrams_count.items():
            for letter, count in following_letter.items():
                if following_letter[letter] == 0:
                    zeros += 1
                else:
                    non_zeros += 1

        return round((zeros / (zeros + non_zeros)) * 100, 5)

    def add_k_smoothing(self, k=1):
        for letter, preceding_bigrams in self.trigrams_count.items():
            for preceding_bigram, count in preceding_bigrams.items():
                preceding_bigrams[preceding_bigram] += k
        self.k_smoothed = True
        self.k = k

    def generate_random_output(self, length=300, export_to_file=False):
        """
        Generates a random output according
        to the generated language model.
        :param export_to_file: True if you want to export the result into a file.
        :param length: Length k (3 < k < 300), according to its probabilistic model
        """
        # Step 1. We choose a random trigram starting with one or two underscores.
        w = random.choice([bigram for bigram in self.trigrams_normalized.keys() if bigram.startswith('_')])
        text = w
        for i in range(length):
            # Step 2. for a given length k, now choose
            #         a random bigram (w, x) according to its probability
            current_bigram = self.trigrams_normalized[w]
            possible_letters = [(k, v) for k, v in current_bigram.items()]
            text += self.generate_random_from(possible_letters)
            w = text[-2:]
            # And so on, until the string reaches the desired length

        text = text.replace("__", " ").replace("_", "")
        print(ANSI.bold, "➤➤➤ Random output for the language model:", ANSI.endc)
        print("    ", text)
        if export_to_file:
            path = "random_output_" + os.path.basename(self.path_file)
            print(ANSI.bold, "➤➤➤ Random output successully exported.", ANSI.endc)
            print("     Path to random output: ", ANSI.ok_green, path, ANSI.endc)
            with open(path, 'w') as file:
                file.write(text)

        return text

    def compute_perplexity(self, text):
        """
        Gives the perplexity of a text regarding the current language model.
        :param text: the text to evaluate
        :return: The perplexity of a text according to the current language model.
        :rtype: float
        """
        text_cleaned = self.clean_text(text.split("\t")[1])

        # Computation of the perplexity
        start, offset = 0, 2
        index_current_letter = 2
        p = 1.0
        while index_current_letter < len(text_cleaned):
            p *= (1/self.trigrams_normalized[text_cleaned[start:offset]][text_cleaned[index_current_letter]])
            start += 1
            offset += 1
            index_current_letter += 1
        return p ** (1/len(text_cleaned))

    @staticmethod
    def generate_all_trigrams():
        """
        Generates all possible bigram
        """
        z = {}
        alphabet = "abcdefghijklmnopqrstuvwxyz_"
        for first_letter in alphabet:
            for second_letter in alphabet:
                z[first_letter + second_letter] = {}

                for third_letter in alphabet:
                    z[first_letter + second_letter][third_letter] = 0
        return z

    @staticmethod
    def generate_random_from(possible_letters):
        """
        Generates a random 
        :parameter possible_letters: The list of (letter, corresponding proba).
        """
        # As the probabilities does not sum to 1, our random will not be
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

        # The following instructions should never be reachable
        # but in case of doubt, I put them anyway.
        print(ANSI.fail, "It seems that I could not generate a random letter", ANSI.endc)
        return random.choice(possible_letters)[0]

    @staticmethod
    def clean_text(text):
        """
        Cleans a text.
        :parameter text: the text to clean
        """
        text = regexp.sub(" ", "__", text.lower(), flags=regexp.MULTILINE)
        return "_" + regexp.sub("[^_a-zA-Z]", "", text, flags=regexp.MULTILINE) + "_"


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
