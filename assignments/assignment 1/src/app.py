from src.TextProcessor import TextProcessor

"""
Python like "main function"
"""
if __name__ == '__main__':
    text_processor = TextProcessor("../training_set/training.GB")
    text_processor.generate_trigrams_probabilities()
    print("Percentage of zeros: ", text_processor.percentage_of_zeros(), "%")
    text_processor.add_one_smoothing()
    text_processor.export()
