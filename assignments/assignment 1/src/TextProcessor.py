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
        self.text_has_changed = False
        self.trigrams_count = None
        self.trigrams_probabilities = None
        # Will contains all the sequence of word of the text
        self.text_as_array = None
        self.count_total_trigrams = 0
        print("Text file successfully imported in the memory...")
        self.clean_text()
        print("The text has been cleaned according to the given instructions...")
        self.count_letter_trigrams()
        print("Trigrams letter have been made...")
        print("Total amount of trigrams : ", self.count_total_trigrams)
        self.generate_statistics()
        print("Probabilities over trigrams successfully generated !")
        file.close()

    """
    Clean the text without modifying the input file.
    The function transforms all non-char characters
    to double underscores.
    """
    def clean_text(self):
        self.text = regexp.sub(" ", "__", self.text.lower(), flags=regexp.MULTILINE)
        self.text = regexp.sub("[^_a-zA-Z]", "", self.text, flags=regexp.MULTILINE)
        self.text_as_array = list(filter(None, self.text.split("_")))
        # we remove bigrams
        self.text_as_array = [i for i in self.text_as_array if len(i) > 2]

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
            json.dump(self.trigrams_probabilities, file)

    """
    Counts all letter 3-grams
    """
    def count_letter_trigrams(self):
        self.count_total_trigrams = 0
        if self.trigrams_count is None or self.text_has_changed:
            self.trigrams_count = {}
            # Count all letter 3-gram
            for word in self.text_as_array:
                start, end = 0, 3

                if len(word) >= 3:
                    while end < len(word):
                        if word[start:end] not in self.trigrams_count.keys():
                            self.trigrams_count[word[start:end]] = 1
                        else:
                            self.trigrams_count[word[start:end]] += 1
                        start += 1
                        end += 1
                        self.count_total_trigrams += 1
                else:
                    if word not in self.trigrams_count.keys():
                        self.trigrams_count[word] = 1
                    else:
                        self.trigrams_count[word] += 1
                        self.count_total_trigrams += 1
        return self.trigrams_count

    def generate_statistics(self):
        if self.trigrams_probabilities is None or self.text_has_changed:
            self.trigrams_probabilities = {}
            # Count all letter 3-gram
            if self.trigrams_count is None or self.text_has_changed:
                self.count_letter_trigrams()

            for word, count in self.trigrams_count.items():
                self.trigrams_probabilities[word] = count / self.count_total_trigrams

        return self.trigrams_probabilities
