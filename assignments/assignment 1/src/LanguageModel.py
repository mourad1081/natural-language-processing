import random
import re as regexp
import json
from operator import itemgetter


class LanguageModel:

    """
    :param path_file Path to the file to process.
    """
    def __init__(self, path_file):

        self.path_file = path_file
        file = open(path_file, "r", encoding="utf-8")
        self.text = "".join(file.readlines())

        self.vocabulary = None
        self.trigrams_count = None
        self.trigrams_probabilities = None
        self.smoothed = False

        self.clean_text()
        self.generate_vocabulary()

        file.close()

    """
    Clean the text without modifying the input file.
    The function transforms all non-char characters
    to double underscores.
    """
    def clean_text(self):
        print(' ➤➤➤ Cleaning text...', end='', flush=True)
        self.text = regexp.sub(" ", "__", self.text.lower(), flags=regexp.MULTILINE)
        self.text = regexp.sub("[^_a-zA-Z]", "", self.text, flags=regexp.MULTILINE)
        print(ANSI.ok_green, 'OK ✓', ANSI.endc)

    """
    Prints the whole corpus.
    """
    def __str__(self):
        return self.text

    """
    Exports the current state of the text in a file.
    """
    def export(self):
        if self.trigrams_probabilities is not None:
            with open(self.path_file + "__results.json", 'w') as file:
                json.dump(self.trigrams_probabilities, file, indent=4)
            print(ANSI.bold, "➤➤➤ Language model successfully generated.", ANSI.endc)
            print("     Path to language model: ", ANSI.ok_green, self.path_file + "__results.json", ANSI.endc)

    """
    Generates the vocabulary of the text.
    """
    def generate_vocabulary(self):
        print(' ➤➤➤ Generating vocabulary...', end='', flush=True)
        self.vocabulary = {}
        for letter in self.text:
            if letter not in self.vocabulary.keys():
                self.vocabulary[letter] = 1
            else:
                self.vocabulary[letter] += 1
        print(ANSI.ok_green, 'OK ✓', ANSI.endc)

    """
    Counts all letter 3-grams
    """
    def generate_trigrams_counts(self):
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

    """
    Transform the matrix to a language model.
    @:param logspace True if you want to produce the log 
            of the probabilities instead of the raw ones.
            It is useful in order to avoid underflows.
    """
    def generate_trigram_probabilities(self):
        print(' ➤➤➤ Generating trigram probabilities...', end='', flush=True)
        self.trigrams_probabilities = self.generate_all_trigrams()
        for bigram, following_letter in self.trigrams_count.items():
            for letter, count in following_letter.items():
                probability = self.trigrams_count[bigram][letter] / self.vocabulary[letter]
                self.trigrams_probabilities[bigram][letter] = probability
        print(ANSI.ok_green, 'OK ✓', ANSI.endc)

    """
    Returns the percentage of zeros in the matrix.
    @:return The percentage (between 0 and 100).
    """
    def percentage_of_zeros(self):
        if self.smoothed:
            print(ANSI.warning, "➤➤➤ WARNING: As you already smoothed the counts, there will be 0 zeros.", ANSI.endc)
        zeros, non_zeros = 0, 0
        for bigram, following_letter in self.trigrams_count.items():
            for letter, count in following_letter.items():
                if following_letter[letter] == 0:
                    zeros += 1
                else:
                    non_zeros += 1

        return round((zeros / (zeros + non_zeros)) * 100, 5)

    """
    Laplace smoothing, also called Add-1 smoothing.
    Smooths the probabilites of a trigram by adding
    1 to each trigram of the matrix.
    """
    def add_one_smoothing(self):
        for letter, preceding_bigrams in self.trigrams_count.items():
            for preceding_bigram, count in preceding_bigrams.items():
                preceding_bigrams[preceding_bigram] += 1
        self.smoothed = True

    """
    Generates a random output according
    to the generated language model.
    @:param length Length k (3 < k < 300), 
            according to its probabilistic model
    """
    def generate_random_output(self, length=300):
        # Step 1. We choose a random trigram starting with one or two underscores.
        w = random.choice([bigram for bigram in self.trigrams_probabilities.keys() if bigram.startswith('_')])
        text = w
        for i in range(length):
            # Step 2. for a given length k, now choose
            #         a random bigram (w, x) according to its probability
            current_bigram = self.trigrams_probabilities[w]
            possible_letters = [(k, v) for k, v in current_bigram.items()]
            text += self.generate_random_from(possible_letters)
            w = text[-2:]
            # And so on, until the string reaches the desired length
        return text

    """
    Generates all possible bigram
    """
    @staticmethod
    def generate_all_trigrams():
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
        # As the probabilities does not sum to 1, our random will not be
        # in the range 0...1, but 0... sum(probas of possible_letters)
        possible_letters.sort(key=itemgetter(1))
        r = random.uniform(0, sum([item[1] for item in possible_letters]))
        cpt = 0.0
        for item in possible_letters:
            cpt += item[1]
            if r < cpt:
                return item[0]

        # This situation should never be reachable
        # but in case of doubt, I put it anyway.
        print(ANSI.fail, "It seems that I could not generate a random letter", ANSI.endc)
        return random.choice(possible_letters)[0]


# Just for printing colors
class ANSI:
    header = '\033[95m'
    ok_blue = '\033[94m'
    ok_green = '\033[92m'
    warning = '\033[93m'
    fail = '\033[91m'
    endc = '\033[0m'
    bold = '\033[1m'
    underline = '\033[4m'
