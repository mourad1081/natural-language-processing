import re
import numpy as np
import random
import math

def simplification(filename):
    f = open(filename, encoding="utf8" )
    alist = f.readlines()
    alist = ''.join(alist)
    # alist = 'I love NLP'
    alist = re.sub(r'[^a-z]+','__', alist.lower())
    alist = '__'+alist+'__'
    return alist

def create_trigram(main_string):
    p = dict()
    lengthMain = len(main_string)

    for i in range(2,lengthMain+1):
        bigram = main_string[i-2] + main_string[i-1]
        if i < lengthMain:
            trigram = bigram + main_string[i]
            if trigram in p:
                p[trigram] += 1
            else:
                p[trigram] = 1
        if bigram in p:
            p[bigram] += 1
        else:
            p[bigram] = 1
    return p


def create_output_proba(filename,prob):
    out = open('LM'+filename,'w+')
    for item in prob:
        out.write("%s %s  \n" % (item,prob[item]))


def computeProba(main_string,p):
    proba = dict()
    lengthMain = len(main_string)
    # PROBABILITY
    for i in range(2,lengthMain+1):
        bigram = main_string[i - 2] + main_string[i - 1]
        if i < lengthMain:
            letter_i = main_string[i]
            trigram = bigram + letter_i
            if not (bigram in proba):
                proba[bigram] = dict()

            proba[bigram][letter_i] = (p[trigram]/p[bigram])
    return proba


def categorie_proba(proba,start_bigram,values):
    stop = False
    i = 0
    r = random.random()
    ind = 0
    uniform = np.random.uniform(0,1,len(values))
    uniform.sort()
    while i < len(proba[start_bigram])-1 and (not stop):
        if r > uniform[i] and r < uniform[i+1]:
            stop = True
            ind = i
        i += 1
    return ind


def generate_text():
    k = np.random.randint(4,300)
    text = '__'
    last_letter = ''
    stop = False
    length_text = len(text)
    while k > 0 and (not stop):
        bigram = text[length_text-2] + text[length_text-1]
        values = []
        keys = []
        for key in proba[bigram]:
            values.append(proba[bigram][key])
            keys.append(key)

        ind = categorie_proba(proba, bigram,values)
        new_letter = keys[ind]
        text += new_letter
        if(new_letter != '_'):
            k -= 1
        if(new_letter == '_') and (last_letter == '_') and (k <= 0):
            stop = True
        last_letter = new_letter
        length_text = len(text)
    print('-------------')
    text = re.sub('__', ' ', text)
    print(text)


def perplexity(filename, proba,text_langage):
    # PERPLEXITY
    for ind in range(len(text_langage)):
        text = text_langage[ind]
        for i in range(len(text)):
            nb_trigram = 0
            probabilities = []
            proba_text = 1
            for j in range(2, len(text)):
                letter = text[j]
                bigram = text[j - 2] + text[j - 1]
                if letter in proba[bigram]:
                    probabilities.append(proba[bigram][letter])
                nb_trigram += 1

            for tmp in probabilities:
                proba_text *= tmp

            perplexity_text = math.pow(proba_text,(-(1/nb_trigram)))

        print(filename +' : '+ str(perplexity_text))
        print('---------------------------------')


if __name__ == "__main__":
    f = open('../test_set/test', encoding="utf8")
    text_file = []
    alist = f.readlines()
    for i in range(len(alist)):
        text_file.append(''.join(alist[i]))
        text_file[i] = re.sub(r'[^a-z]+', '__', text_file[i].lower())
        text_file[i] = '__' + text_file[i]

    filenames = ['../training_set/training.AU', '../training_set/training.GB', '../training_set/training.US']
    cpt = 3
    for i in range(len(filenames)):
        print('File : ' + filenames[i])
        print('--------------------------------------')
        main_string = simplification(filenames[i])
        p = create_trigram(main_string)
        proba = computeProba(main_string,p)
        create_output_proba(filenames[i][9:11],proba)
        generate_text()
        perplexity(filenames[i],proba,text_file)
