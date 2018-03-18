import re as regexp
import json


class TextProcessor:

    """
    :param path_file Path to the file to process.
    """
    def __init__(self, path_file):
        self.path_file = path_file
        file = open(path_file, "r", encoding="utf-8")
        self.text = "".join(file.readlines())
        self.vocabulary = None
        self.trigrams_count = None
        print('==> Cleaning text...')
        self.clean_text()
        print('==> Generating vocabulary...')
        self.generate_vocabulary()

        file.close()

    """
    Clean the text without modifying the input file.
    The function transforms all non-char characters
    to double underscores.
    """
    def clean_text(self):
        self.text = regexp.sub(" ", "__", self.text.lower(), flags=regexp.MULTILINE)
        self.text = regexp.sub("[^_a-zA-Z]", "", self.text, flags=regexp.MULTILINE)
        # we remove bigrams

    """
    Prints the whole text at its current state.
    """
    def __str__(self):
        return self.text

    """
    Exports the current state of the text in a file.
    """
    def export(self):
        with open(self.path_file + "__results.json", 'w') as file:
            json.dump(self.trigrams_count, file)

    """
    Generates the vocabulary of the text.
    """
    def generate_vocabulary(self):
        self.vocabulary = {}
        for letter in self.text:
            if letter not in self.vocabulary.keys():
                self.vocabulary[letter] = 1
            else:
                self.vocabulary[letter] += 1

    """
    Counts all letter 3-grams
    """
    def generate_trigrams_probabilities(self):
        # We create a 2D matrix : column = P(w_i | w_i-2, w_i-1)
        self.trigrams_count = {}
        start, offset_bigram, i = 0, 2, 2

        while i < len(self.text):
            preceding_bigram = self.text[start:offset_bigram]
            current_letter = self.text[i]
            if self.text[i] not in self.trigrams_count.keys():
                self.trigrams_count[current_letter] = {}
                # Generate all possible bigrams for that letter if not already seen
                for x in "abcdefghijklmnopqrstuvwxyz_":
                    for y in "abcdefghijklmnopqrstuvwxyz_":
                        self.trigrams_count[current_letter][x + y] = 0
            self.trigrams_count[current_letter][preceding_bigram] += 1

            start += 1
            offset_bigram += 1
            i += 1
            if i % 100000 == 0:
                print("Processed", i, "letters")

    def normalize_trigram_probabilities(self):
        pass

    def percentage_of_zeros(self):
        zeros, non_zeros = 0, 0
        for letter, preceding_bigrams in self.trigrams_count.items():
            for preceding_bigram, count in preceding_bigrams.items():
                if preceding_bigrams[preceding_bigram] == 0:
                    zeros += 1
                else:
                    non_zeros += 1

        return zeros / (zeros + non_zeros)

    def add_one_smoothing(self):
        for letter, preceding_bigrams in self.trigrams_count.items():
            for preceding_bigram, count in preceding_bigrams.items():
                preceding_bigrams[preceding_bigram] += 1

    def generate_statistics(self):
        pass
