from sklearn.model_selection import GridSearchCV
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import pyLDAvis.gensim
import pyLDAvis.sklearn
import pickle

from .Cleaner import Cleaner


class LDA_wrapper():

    def __init__(self):
        # algunas palabras comunes, poco relevantes (saque muchas a mano que eran interesantes)
        with open("r_words.txt", 'r') as myfile:
            common_words = [line.replace('\n', '') for line in myfile.readlines()]

        self.common_words = common_words
        #self.stemming_dict_ = {}
        #self.cleaner = Cleaner()
        #self.data_clean = self.cleaner.data_clean

    def data_vectorizer(self, data, stem, lowercase=True, min_df=5, max_df=.65, token_pattern='[a-zA-Z][a-zA-Z]{2,}'):
        vectorizer = CountVectorizer(lowercase=lowercase, min_df=min_df, max_df=max_df,
                                     token_pattern=token_pattern)
        ## En Gensim
        ##filter_extremes para sacar las palabras que aparecen mucho o muy poco
        ##dictionary.filter_extremes()

        #data_vectorized = vectorizer.fit_transform(self.data_clean(data, stemming=stem))
        # Ya hacemos la limpieza antes de pasarle los datos.
        data_vectorized = vectorizer.fit_transform(data)

        self.vectorizer = vectorizer
        return data_vectorized, vectorizer

    def lda(self, data, n_components=None, max_iter=100, batch_size=50, learning_method='online', stemming=True):

        if n_components is None:
            lda_model, ntopics = self.ntopics(data, min_topics=3, max_topics=20, max_iter=50, learning_method='online')

        else:
            ## Hay que probar aumentar la cantidad de iteraciones
            lda_model = LatentDirichletAllocation(n_components=n_components,
                                                  max_iter=max_iter,
                                                  #batch_size=batch_size,
                                                  learning_method=learning_method,
                                                  verbose=True,
                                                  random_state=1234)
            data_vectorized, _ = self.data_vectorizer(data, stem=stemming)
            lda_model.fit(data_vectorized)

        self.lda_model = lda_model
        self.stemming = stemming
        return lda_model, stemming

    def ntopics(self, data, min_topics=3, max_topics=20, max_iter=50, learning_method='online', stemming = True):
        # Define Search Param
        search_params = {'n_components': list(range(min_topics, max_topics))}
        # Init the Model
        lda = LatentDirichletAllocation(max_iter=max_iter, learning_method=learning_method)
        # Init Grid Search Class
        model = GridSearchCV(lda, param_grid=search_params, verbose=True)
        # Do the Grid Search
        data_vectorized, _ = self.data_vectorizer(data, stem = stemming)
        model.fit(data_vectorized)
        best_model = model.best_estimator_
        ntopics = model.best_params_['n_components']
        return best_model, ntopics

    def lda_vis(self, lda_model, data_vectorized, vectorizer):

        pyLDAvis.enable_notebook()
        vis = pyLDAvis.sklearn.prepare(lda_model, data_vectorized, vectorizer, mds='tsne')
        return vis

    def topic_keyowrd_matrix(self, lda_model, vectorizer):

        topicnames = ["Topic" + str(i) for i in range(lda_model.n_components)]

        # Topic-Keyword Matrix
        df_topic_keywords = pd.DataFrame(lda_model.components_)

        # Assign Column and Index
        df_topic_keywords.columns = vectorizer.get_feature_names()
        df_topic_keywords.index = topicnames
        return df_topic_keywords

    def display_topics(self, model=None, feature_names=None, no_top_words=10, subset=None):

        if model is None:
            model = self.lda_model

        if feature_names is None:
            feature_names = self.vectorizer.get_feature_names()

        if subset is None:
            subset = range(model.components_.shape[0])
        for i in subset:
            topic = model.components_[i]
            print("Topic %d:" % (i))
            print(" ".join([feature_names[j] for j in topic.argsort()[:-no_top_words - 1:-1]]))

    def save_model(self, model, file_name):
        with open(file_name, 'wb') as handle:
            pickle.dump(model, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def restore_model(self, file_name):
        with open(file_name, 'rb') as handle:
            model = pickle.load(handle)
        return model
