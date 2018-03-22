from src.LanguageModel import LanguageModel, ANSI


def generate_language_model(path):
    print(ANSI.header, "Training", path, "corpus")
    print(" -------------------------------------------", ANSI.endc)
    lm = LanguageModel(path)

    lm.generate_trigrams_counts()

    k = 2 if path.endswith("AU") else 1.2 if path.endswith("GB") else 1.8
    lm.add_k_smoothing(k=k)
    lm.maximum_likelihood()

    lm.export()
    lm.generate_random_output(length=200, export_to_file=True)
    print("\n")
    return lm


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

    # We create the LM's
    language_models = []
    for corpus in training_set:
        language_models.append(generate_language_model(corpus))

    # We classify the test set
    for test in test_set:
        file = open(test, 'r')
        perplexities = {}
        i = 0
        for line in file.readlines():
            perplexities['line ' + str(i)] = {}
            print(ANSI.ok_blue, "Line to classify (results below):")
            print("➤➤➤", line[:50] + '...', ANSI.endc)
            print(" ➤➤➤ Results:")
            print(" -----------")
            for lmodel in language_models:
                perplexities['line ' + str(i)][lmodel.name] = lmodel.get_perplexity_from(line)
                print(" ➤➤➤ Perplexity of", lmodel.name, "=", perplexities['line ' + str(i)][lmodel.name])

            x = min(perplexities['line ' + str(i)].keys(), key=(lambda k: perplexities['line ' + str(i)][k]))
            print(ANSI.header, '★★★★★★★★ Best result:', x, '★★★★★★★★★★', ANSI.endc)
            i += 1

        file.close()
