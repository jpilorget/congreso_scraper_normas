from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import unicodedata2
import string
from sklearn.model_selection import GridSearchCV
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import pyLDAvis.gensim
import pyLDAvis.sklearn
import re
import pickle


class LDA_wrapper():
    
    def __init__(self):
        #algunas palabras comunes, poco relevantes (saque muchas a mano que eran interesantes)
        with open("removable.txt", 'r') as myfile:
            common_words=[line.replace('\n', '') for line in myfile.readlines()]

        self.common_words = common_words
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
        stop_words = stopwords.words(stopwords_lang)
        remove_words  = set(stop_words).union(set(self.common_words))
        remove_punctuation_map = dict((ord(char), ' ') for char in string.punctuation)
        doc = self.strip_accents(doc).lower()
        doc = doc.translate(remove_punctuation_map)
        querywords = doc.split()
        filtered_words = [palabra for palabra in querywords if palabra not in remove_words]       
        if stem:
            doc = self.stemmer(filtered_words)
        else:
            doc = (' ').join(filtered_words)
        return doc
    
    def data_clean(self,data, stemming):
        data_clean = [self.preprocess(doc, stem = stemming) for doc in data]
        if stemming:
            data_clean = self.de_stemmer(data_clean)
        return data_clean
    
    def vectorizer(self,data,stem, lowercase=True, min_df= 5, max_df= .65,token_pattern='[a-zA-Z][a-zA-Z]{2,}'):
        vectorizer = CountVectorizer(lowercase=lowercase, min_df= min_df, max_df=max_df,
                             token_pattern=token_pattern)
        data_vectorized = vectorizer.fit_transform(self.data_clean(data, stemming = stem ))
        
        self.vectorizer = vectorizer
        return data_vectorized, vectorizer

    def lda(self,data,n_components=None, max_iter=50, learning_method='online', stemming = False):
        
        if n_components is None:
            lda_model, ntopics = self.ntopics(data,min_topics=3, max_topics=20,max_iter=50, learning_method='online')
        
        else:
            lda_model = LatentDirichletAllocation(n_components=n_components, max_iter=max_iter, learning_method=learning_method)
            data_vectorized,_ = self.vectorizer(data, stem = stemming) 
            lda_model.fit(data_vectorized)
        
        self.lda_model = lda_model
        self.stemming = stemming
        return lda_model, stemming

    
    def ntopics(self,data, min_topics=3, max_topics=20,max_iter=50, learning_method='online'):
        # Define Search Param
        search_params = {'n_components': list(range(min_topics, max_topics))}
        # Init the Model
        lda = LatentDirichletAllocation(max_iter = max_iter, learning_method=learning_method)
        # Init Grid Search Class
        model = GridSearchCV(lda, param_grid=search_params,verbose=True)
        # Do the Grid Search
        data_vectorized,_ = self.vectorizer(data) 
        model.fit(data_vectorized)
        best_model = model.best_estimator_
        ntopics = model.best_params_['n_components']
        return best_model, ntopics
    
    def lda_vis(self,lda_model,data_vectorized, vectorizer):
        
        pyLDAvis.enable_notebook()
        vis = pyLDAvis.sklearn.prepare(lda_model,data_vectorized,vectorizer, mds='tsne')
        return vis
    
    def topic_keyowrd_matrix(self, lda_model,vectorizer):
        
        topicnames = ["Topic" + str(i) for i in range(lda_model.n_components)]

        # Topic-Keyword Matrix
        df_topic_keywords = pd.DataFrame(lda_model.components_)

        # Assign Column and Index
        df_topic_keywords.columns = vectorizer.get_feature_names()
        df_topic_keywords.index = topicnames
        return df_topic_keywords
    
    def display_topics(self,model = None, feature_names = None, no_top_words= 10, subset= None):
        
        if model is None:
            model = self.lda_model
        
        if feature_names is None:
            feature_names = self.vectorizer.get_feature_names()
        
        if subset is None:
            subset = range(model.components_.shape[0])
        for i in subset:
            topic = model.components_[i]
            print("Topic %d:" % (i))
            print( " ".join([feature_names[j] for j in topic.argsort()[:-no_top_words - 1:-1]]))
    
    def save_model(self, model, file_name):
        with open(file_name, 'wb') as handle:
            pickle.dump(model, handle, protocol=pickle.HIGHEST_PROTOCOL)
    
    def restore_model(self, file_name):
        with open(file_name, 'rb') as handle:
            model = pickle.load(handle)
        return model
