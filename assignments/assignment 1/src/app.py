from src.TextProcessor import TextProcessor

"""
Python like "main function"
"""
if __name__ == '__main__':
    text_processor = TextProcessor("../training_set/training.GB")
    text_processor.export()
