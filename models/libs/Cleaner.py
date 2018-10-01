from tqdm import tqdm
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import unicodedata2
import string



class Cleaner:
    
    def __init__(self):
        with open("r_words.txt", 'r') as r_w_files:
            common_words=[line.replace('\n', '') for line in r_w_files.readlines()]
        with open("r_sentences.txt", 'r') as r_s_files:
            common_sentences=[line.replace('\n', '') for line in r_s_files.readlines()]    
        self.common_words = common_words
        self.common_sentences = common_sentences
        self.stemming_dict_ = {}

    
    def strip_accents(self, text):
        text = unicodedata2.normalize('NFD', text)
        text = text.encode('ascii', 'ignore')
        text = text.decode("utf-8")
        return str(text)
    
    def stemmer(self, filtered_words):
        stemmer = SnowballStemmer('spanish')
        stemmed_words = []
        for i in filtered_words:
            stemmed = stemmer.stem(i)
            stemmed_words.append(stemmed)
            if stemmed in self.stemming_dict_:
                dict_stem = self.stemming_dict_[stemmed]
                if i in dict_stem:
                    dict_stem[i] =  dict_stem[i] + 1
                else:
                    dict_stem[i] = 1
            else:
                 self.stemming_dict_[stemmed] = {i:1}
        doc = (' ').join(stemmed_words)
        return  doc
    
    def de_stemmer(self, data):
        #busco el mas frecuente
        replacement = {}
        for key in tqdm(self.stemming_dict_.keys(), desc="select most representative word of stem"):
            stem_dict = self.stemming_dict_[key]
            replacement[key] = max(stem_dict, key=stem_dict.get)
        self.replacement = replacement
        #remplazo en los documentos
        de_stemmed = []
        for doc in tqdm(data, desc = "de-stemming"):
            word_list = doc.split(' ')
            new_list = []
            for word in word_list:
                if word in self.stemming_dict_:
                    new_list.append(replacement.get(word))
                else:
                    new_list.append(word)
            de_stemmed.append(' '.join(new_list))


        return de_stemmed
    
    
    def preprocess(self, doc,stem, stopwords_lang = "spanish"):
        for frase in self.common_sentences:
            doc=doc.replace(frase, '')
        stop_words = stopwords.words(stopwords_lang)
        remove_words  = set(stop_words).union(set(self.common_words))
        remove_punctuation_map = dict((ord(char), ' ') for char in string.punctuation)
        doc = self.strip_accents(doc).lower()
        doc = doc.translate(remove_punctuation_map)
        querywords = doc.split()
        #Agrego replacement de numeros por NUM
        querywords = ["NUM" if c.isdigit() else c for c in querywords]
        filtered_words = [palabra for palabra in querywords if palabra not in remove_words]       
        if stem:
            doc = self.stemmer(filtered_words)
        else:
            doc = (' ').join(filtered_words)
        return doc
    
    def data_clean(self,data, stemming):
        data_clean = [self.preprocess(doc, stem = stemming) for doc in tqdm(data, desc = "preprocess")]
        if stemming:
            data_clean = self.de_stemmer(data_clean)
        return data_clean
    
