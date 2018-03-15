import re as regexp


class TextProcessor:
    """
    :param path_file Path to the file to process.
    """
    def __init__(self, path_file):
        file = open(path_file, "r", encoding="utf-8")
        self.text = "".join(file.readlines())
        file.close()

    """
    Clean the text without modifying the input file.
    The function transforms all non-char characters
    to double underscores.
    """
    def clean_text(self):
        self.text = regexp.sub(" ", "__", self.text.lower(), flags=regexp.MULTILINE)
        self.text = regexp.sub("[^_a-zA-Z]", "", self.text, flags=regexp.MULTILINE)

    """
    Prints the whole text at its current state.
    """
    def __str__(self):
        return self.text

    """
    Exports the current state of the text in a file.
    """
    def export(self, path_file="../output/result.txt"):
        file = open(path_file, "wt", encoding="utf-8")
        file.write(self.text)
        file.close()
