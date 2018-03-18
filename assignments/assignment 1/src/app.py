from src.LanguageModel import LanguageModel, ANSI


def train_and_export(path):
    print(ANSI.header, "Training", path, "corpus")
    print(" -------------------------------------------", ANSI.endc)
    lm = LanguageModel(path)
    lm.generate_trigrams_counts()
    lm.generate_trigram_probabilities()
    lm.add_one_smoothing()
    lm.export()
    print(lm.generate_random_output().replace("__", " ").replace("_", ""))
    print("\n")


"""
Python-like "main function"
"""
if __name__ == '__main__':
    training_set = [
        "../training_set/training.GB",
        "../training_set/training.AU",
        "../training_set/training.US"
    ]

    test_set = ["../test_set/test"]

    for corpus in training_set:
        train_and_export(corpus)