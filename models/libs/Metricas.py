import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import string
from tqdm import tqdm
import numpy as np
from gensim.matutils import corpus2dense
from scipy.stats import fisher_exact
from .Cleaner import Cleaner



class Metricas():

    def __init__(self, df, dictionary, replacement = None, stem=False):
        self.dictionary = dictionary
        self.dict_totals = self.armo_dic(df)
        self.N_df = self.totales_revista()
        self.replacement = replacement
        self.stem = stem
        self.cleaner = Cleaner()

    def armo_dic(self, df):
        dict_totals = {}
        for yr in tqdm(df["year"].unique()):
            dict_totals[yr] = {}
            for revista in ["brando", "ohlala"]:
                tmp_df = df[(df["year"] == yr) & (df["revista"] == revista)]
                bow = tmp_df.bow
                dense = corpus2dense(bow, len(self.dictionary.items()))
                total_per_word = dense.sum(axis=1)
                dict_totals[yr][revista] = total_per_word

        return dict_totals

    def clean_word(self, palabra, stopwords_lang="spanish"):
        stop_words = stopwords.words(stopwords_lang)
        remove_words = set(stop_words).union(set(self.cleaner.common_words))
        remove_punctuation_map = dict((ord(char), ' ') for char in string.punctuation)
        palabra = self.cleaner.strip_accents(palabra).lower()
        palabra = palabra.translate(remove_punctuation_map)
        palabra = "NUM" if palabra.isdigit() else palabra
        palabra = "" if palabra in remove_words else palabra

        if self.stem:
            stemmer = SnowballStemmer('spanish')
            stemmed = stemmer.stem(palabra)
            try:
                palabra = self.replacement.get(stemmed)
            except:
                print("word not in dictionary of stems")
                palabra = ""

        return palabra

    def totales_palabra(self, idx):
        n_df = pd.DataFrame.from_dict(self.dict_totals, orient='index')
        n_df["brando"] = n_df.apply(lambda x: x["brando"][idx], 1)
        n_df["ohlala"] = n_df.apply(lambda x: x["ohlala"][idx], 1)
        return n_df

    def totales_revista(self):

        N_df = pd.DataFrame.from_dict(self.dict_totals, orient='index')
        N_df_B = N_df["brando"].apply(lambda x: x.sum())
        N_df_O = N_df["ohlala"].apply(lambda x: x.sum())
        N_df = pd.concat([N_df_B, N_df_O], axis=1)
        return N_df

    def score(self, n_brando, n_ohlala, N_brando, N_ohlala):
        p_brando = n_brando / N_brando
        p_ohlala = n_ohlala / N_ohlala
        sum_p = p_brando + p_ohlala
        score_brando = p_brando / sum_p
        score_ohlala = p_ohlala / sum_p
        return score_brando, score_ohlala

    def proba(self, n_brando, n_ohlala, N_brando, N_ohlala):
        p_brando = n_brando / N_brando
        p_ohlala = n_ohlala / N_ohlala
        return p_brando, p_ohlala

    def odd(self, n_brando, n_ohlala, N_brando, N_ohlala):
        p_brando = (n_brando+1) / (N_brando+1)
        p_ohlala = (n_ohlala+1) / (N_ohlala+1)
        score_brando = p_brando / p_ohlala
        score_ohlala = p_ohlala / p_brando
        return score_brando, score_ohlala

    def score_df(self, palabra):
        palabra = self.clean_word(palabra)
        idx = self.dictionary.token2id[palabra]
        n_df = self.totales_palabra(idx)
        N_df = self.N_df

        scores = {}
        for yr in N_df.index:
            scores[yr] = {}
            N_b = N_df.loc[yr, "brando"]
            N_o = N_df.loc[yr, "ohlala"]
            n_b = n_df.loc[yr, "brando"]
            n_o = n_df.loc[yr, "ohlala"]
            score_b, score_o = self.score(n_b, n_o, N_b, N_o)
            scores[yr]["brando"] = score_b
            scores[yr]["ohlala"] = score_o
        scores_df = pd.DataFrame.from_dict(scores, orient='index')
        scores_df['year'] = scores_df.index
        return scores_df

    def proba_df(self, palabra):
        palabra = self.clean_word(palabra)
        idx = self.dictionary.token2id[palabra]
        n_df = self.totales_palabra(idx)
        N_df = self.N_df

        scores = {}
        for yr in N_df.index:
            scores[yr] = {}
            N_b = N_df.loc[yr, "brando"]
            N_o = N_df.loc[yr, "ohlala"]
            n_b = n_df.loc[yr, "brando"]
            n_o = n_df.loc[yr, "ohlala"]
            score_b, score_o = self.proba(n_b, n_o, N_b, N_o)
            # chi, p_value = chisquare([n_b, n_o])
            oddsratio, p_value = fisher_exact([[n_b, n_o], [N_b - n_b, N_o - n_o]])
            scores[yr]["brando"] = score_b
            scores[yr]["ohlala"] = score_o
            scores[yr]["signif"] = p_value <= 0.05
        scores_df = pd.DataFrame.from_dict(scores, orient='index')
        scores_df['year'] = scores_df.index
        return scores_df

    def proba_df_list(self, palabras):

        palabras_limpias = []
        # armoel df con la primera palabra de la lista
        palabras[0] = self.clean_word(palabras[0])
        idx = self.dictionary.token2id[palabras[0]]
        n_df = self.totales_palabra(idx)

        palabras_limpias.append(palabras[0])
        # Sumo a n_df los dataframe de las demas palabras
        for palabra in palabras[1:]:
            palabra = self.clean_word(palabra)
            idx = self.dictionary.token2id[palabra]
            n_df = n_df + self.totales_palabra(idx)
            palabras_limpias.append(palabra)

        N_df = self.N_df
        scores = {}
        for yr in N_df.index:
            scores[yr] = {}
            N_b = N_df.loc[yr, "brando"]
            N_o = N_df.loc[yr, "ohlala"]
            n_b = n_df.loc[yr, "brando"]
            n_o = n_df.loc[yr, "ohlala"]
            score_b, score_o = self.proba(n_b, n_o, N_b, N_o)
            # chi, p_value = chisquare([n_b, n_o])
            oddsratio, p_value = fisher_exact([[n_b, n_o], [N_b - n_b, N_o - n_o]])
            scores[yr]["brando"] = score_b
            scores[yr]["ohlala"] = score_o
            scores[yr]["signif"] = p_value <= 0.05
        scores_df = pd.DataFrame.from_dict(scores, orient='index')
        scores_df['year'] = scores_df.index
        return scores_df, palabras_limpias

    def odd_df(self, palabra):
        palabra = self.clean_word(palabra)
        idx = self.dictionary.token2id[palabra]
        n_df = self.totales_palabra(idx)
        N_df = self.N_df

        scores = {}
        for yr in N_df.index:
            scores[yr] = {}
            N_b = N_df.loc[yr, "brando"]
            N_o = N_df.loc[yr, "ohlala"]
            n_b = n_df.loc[yr, "brando"]
            n_o = n_df.loc[yr, "ohlala"]
            score_b, score_o = self.odd(n_b, n_o, N_b, N_o)
            scores[yr]["brando"] = score_b
            scores[yr]["ohlala"] = score_o
        scores_df = pd.DataFrame.from_dict(scores, orient='index')
        scores_df['year'] = scores_df.index
        return scores_df

    def oddList_df(self,minProb = 0.001):
        import collections
        odd_list_val = collections.defaultdict(dict)
        odd_list_rev = collections.defaultdict(dict)
        for k in tqdm(self.dictionary.keys()):
            n_df = self.totales_palabra(k)
            N_df = self.N_df
            for yr in N_df.index:
                N_b = N_df.loc[yr, "brando"]
                N_o = N_df.loc[yr, "ohlala"]
                n_b = n_df.loc[yr, "brando"]
                n_o = n_df.loc[yr, "ohlala"]

                if max((n_b/N_b),(n_o/N_o)) < minProb:
                    continue

                score_brando, score_ohlala = self.odd(n_b, n_o, N_b, N_o)
                revistas = ['brando','ohlala']
                valores =  [score_brando, score_ohlala]
                max_val = np.argmax(valores)
                odd_list_val[yr][self.dictionary[k]] = valores[max_val]
                odd_list_rev[yr][self.dictionary[k]] = revistas[max_val]
                
        odd_df_val = pd.DataFrame.from_dict(odd_list_val, orient='columns')
        odd_df_rev = pd.DataFrame.from_dict(odd_list_rev, orient='columns')
        
        return odd_df_val, odd_df_rev
    
    def oddList_yr(self,odd_df_rev, odd_df_val, yr):
        odd_df = odd_df_rev.join(odd_df_val, lsuffix='_rev', rsuffix='_odd')
        odd_df = odd_df.sort_values([yr + '_odd'], ascending=False)[[yr + '_odd',yr + '_rev']]
        return odd_df
    
    def gen_wordList(self, minProb,minOdd):
        brandoList = []
        ohlalaList = []
        odd_df_val, odd_df_rev = self.oddList_df(minProb)
        for y in range(2008,2019):
            temp_oddsList = self.oddList_yr(odd_df_rev, odd_df_val, '{}'.format(y))
            temp_brandoList = temp_oddsList[\
                                            (temp_oddsList['{}_rev'.format(y)] == 'brando') &\
                                            (temp_oddsList['{}_odd'.format(y)] >= minOdd)]
            temp_ohlalaList = temp_oddsList[\
                                            (temp_oddsList['{}_rev'.format(y)] == 'ohlala') &\
                                            (temp_oddsList['{}_odd'.format(y)] >= minOdd)]
            temp_brandoList = list(temp_brandoList.index)
            temp_ohlalaList = list(temp_ohlalaList.index)
            brandoList.extend(temp_brandoList)
            ohlalaList.extend(temp_ohlalaList)
        return brandoList, ohlalaList
    
    def plot_wordCloud(self,df,rev,quitar,filtro, collocations = True):
        stops = {'NUM','tambien','asi','adema','ademas','ano'}
        stops.update(quitar)
        from wordcloud import WordCloud
        text = ''.join(map(str, list(df[(df.revista == rev)]['text_clean'])))
        text_filtered = [''.join(w for w in s.split() if w in filtro) for s in text.split(' ')]
        text_filtered = [w for w in text_filtered if w not in ['']]
        text_filtered = ' '.join(map(str, text_filtered))
        wordcloud = WordCloud(width=1000,height=500,mode = 'RGBA', background_color=None,stopwords = stops, collocations = collocations).generate(text_filtered)
        import matplotlib.pyplot as plt
        plt.figure(figsize=(16,8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
    
    
    def probaList_df(self,minProb = 0.001):
        import collections
        proba_list_val = collections.defaultdict(dict)
        proba_list_rev = collections.defaultdict(dict)
        for k in tqdm(self.dictionary.keys()):
            n_df = self.totales_palabra(k)
            N_df = self.N_df
            for yr in N_df.index:
                N_b = N_df.loc[yr, "brando"]
                N_o = N_df.loc[yr, "ohlala"]
                n_b = n_df.loc[yr, "brando"]
                n_o = n_df.loc[yr, "ohlala"]

                if max((n_b/N_b),(n_o/N_o)) < minProb:
                    continue

                score_brando, score_ohlala = self.proba(n_b, n_o, N_b, N_o)
                revistas = ['brando','ohlala']
                valores =  [score_brando, score_ohlala]
                max_val = np.argmax(valores)
                proba_list_val[yr][self.dictionary[k]] = valores[max_val]
                proba_list_rev[yr][self.dictionary[k]] = revistas[max_val]
                
        proba_df_val = pd.DataFrame.from_dict(proba_list_val, orient='columns')
        proba_df_rev = pd.DataFrame.from_dict(proba_list_rev, orient='columns')
        return proba_df_val, proba_df_rev
    
    def probaList_yr(self, yr,minProb = 0.001):
        proba_df_val, proba_df_rev = self.probaList_df(minProb)
        proba_df = proba_df_rev.join(proba_df_val, lsuffix='_rev', rsuffix='_prob')
        proba_df = proba_df.sort_values([yr + '_prob'], ascending=False)[[yr + '_prob',yr + '_rev']]
        return proba_df
    
    def plot_score(self, palabra):
        score_df = self.score_df(palabra)
        palabra = self.clean_word(palabra)
        # TODO arreglar el gráfico
        # ax = score_df.plot(x=year,
        #                    figsize=(7, 5),
        #                    color=['blue', 'red'], marker='o', linestyle='dashed', title=palabra)
        # ax.set_xlabel('años')
        # ax.set_ylabel('Tasa de aparición de la palabra')
        plot = score_df.plot()
        return plot

    def plot_odd(self, palabra):
        score_df = self.odd_df(palabra)
        palabra = self.clean_word(palabra)
        # TODO arreglar el gráfico
        # ax = score_df.plot(x=year,
        #                    figsize=(7, 5),
        #                    color=['blue', 'red'], marker='o', linestyle='dashed', title=palabra)
        # ax.set_xlabel('años')
        # ax.set_ylabel('Tasa de aparición de la palabra')
        plot = score_df.plot()
        return plot

    def plot_proba(self, palabra):

        if type(palabra) == str:
            score_df = self.proba_df(palabra)
            palabra = self.clean_word(palabra)

        if type(palabra) == list:
            score_df, palabras_limpias = self.proba_df_list(palabra)
            palabra = ", ".join(palabras_limpias)

        #TODO arreglar el gráfico
        # ax = score_df.plot(x=year,
        #                    figsize=(7, 5),
        #                    color=['blue', 'red'], marker='o', linestyle='dashed', title=palabra)
        # ax.set_xlabel('años')
        # ax.set_ylabel('Tasa de aparición de la palabra')
        plot = score_df.plot()
        return plot



