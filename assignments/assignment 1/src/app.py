from src.TextProcessor import TextProcessor

"""
Python like "main function"
"""
if __name__ == '__main__':
    text_processor = TextProcessor("../training_set/training.AU")
    text_processor.clean_text()
    text_processor.export()
