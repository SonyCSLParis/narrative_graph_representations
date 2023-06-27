"""
Training pyrdf2vec for config file with a local GraphDB endpoint
"""
# -*- coding: utf-8 -*-
import yaml
import argparse
import operator
from urllib import parse
import requests

import pandas as pd
from cachetools import cachedmethod
from sklearn.metrics.pairwise import cosine_similarity
from pyrdf2vec.connectors import SPARQLConnector
from pyrdf2vec import RDF2VecTransformer
from pyrdf2vec.graphs import KG
from pyrdf2vec.typings import Response
from pyrdf2vec.walkers import AnonymousWalker, CommunityWalker, HALKWalker, \
    NGramWalker, RandomWalker, SplitWalker, Walker, \
        WalkletWalker, WLWalker
from pyrdf2vec.samplers import ObjFreqSampler, ObjPredFreqSampler, \
    PredFreqSampler, PageRankSampler, Sampler, UniformSampler, WideSampler
from pyrdf2vec.embedders import Embedder, FastText, Word2Vec

LABEL_TO_EMBEDDER = {
    'embedder': Embedder, 'fasttext': FastText,
    'word2vec': Word2Vec
}


LABEL_TO_WALKER = {
    'anonymous': AnonymousWalker, 'community': CommunityWalker,
    'halk': HALKWalker, 'ngram': NGramWalker,
    'random': RandomWalker, 'split': SplitWalker,
    'walker': Walker, 'walklet': WalkletWalker,
    'weisfeiler_lehman': WLWalker
}

LABEL_TO_SAMPLER = {
    'objfreq': ObjFreqSampler, 'objpredfreq': ObjPredFreqSampler, 
    'predfreq': PredFreqSampler, 'pagerank': PageRankSampler,
    'sampler': Sampler, 'uniform': UniformSampler,
    'wide': WideSampler, 
}

DEFAULT_VALUES = {
    'embedder': Word2Vec,
    'epochs': 10,
    'walker': RandomWalker,
    'max_depth': 5,
    'max_walk': 100,
    'with_reverse': True,
    'n_jobs': 1,
    'sampler': UniformSampler
}

class GraphDBConnector(SPARQLConnector):
    """ Modifying Connector to ensure requests can be run
    More info: https://github.com/IBCNServices/pyRDF2Vec/issues/185 """
    async def _fetch(self, query) -> Response:
        url = f"{self.endpoint[:-1]}?query={parse.quote(query)}"
        print(url)
        async with self._asession.get(url, headers=self._headers) as res:
            return await res.json()

    @cachedmethod(operator.attrgetter("cache"))
    def fetch(self, query: str) -> Response:
        url = f"{self.endpoint[:-1]}?query={parse.quote(query)}"

        with requests.get(url, headers=self._headers, timeout=3600) as res:
            # print(res)
            return res.json()

def helper_get_param(key, config, mapping = None):
    """ Either get value in config or default value """
    if key in config and mapping:
        return mapping[config[key]]
    if key in config:
        return config[key]
    return DEFAULT_VALUES[key]

def init_transformer(config):
    """ Init transformer for walk 
    Default values: """
    epochs = helper_get_param(key='epochs', config=config)
    embedder = helper_get_param(
        key='embedder', config=config, mapping=LABEL_TO_EMBEDDER)(epochs=epochs)

    max_depth = helper_get_param(key='max_depth', config=config)
    max_walk = helper_get_param(key='max_walk', config=config)
    with_reverse = helper_get_param(key='with_reverse', config=config)
    n_jobs = helper_get_param(key='n_jobs', config=config)

    sampler = helper_get_param(
        key='sampler', config=config, mapping=LABEL_TO_SAMPLER)()

    walker = helper_get_param(
        key='walker', config=config, mapping=LABEL_TO_WALKER) \
            (max_depth, max_walk, sampler,
             with_reverse=with_reverse, n_jobs=n_jobs)

    verbose = helper_get_param(key='verbose', config=config)

    return RDF2VecTransformer(
        embedder,
        walkers=[walker],
        verbose=verbose
    )





if __name__ == '__main__':
    """ python src/train_pyrdf2vec.py -csv <to-add> -e <to-add> -c <to-add> """
    ap = argparse.ArgumentParser()
    ap.add_argument('-csv', "--csv", required=True,
                    help=".csv files containing the entities in an `entity` column")
    ap.add_argument('-e', "--endpoint", required=True,
                    help="SPARQL Endpont")
    ap.add_argument('-c', "--config", required=True,
                    help=".yaml file for configuring system")
    args_main = vars(ap.parse_args())


    ENTITIES = list(pd.read_csv(args_main["csv"]).entity.values)
    print(ENTITIES)

    with open(args_main["config"], encoding='utf-8') as file:
        CONFIG = yaml.load(file, Loader=yaml.FullLoader)

    SKIP_PREDICATES = CONFIG.get("skip_predicates", set())
    KNOWLEDGE_GRAPH = KG(
        args_main["endpoint"],
        skip_predicates=set(SKIP_PREDICATES),
        literals=CONFIG.get('literals', []))
    KNOWLEDGE_GRAPH.connector =GraphDBConnector(args_main["endpoint"])

    TRANSFORMER = init_transformer(config=CONFIG)

    EMBEDDINGS, _ = TRANSFORMER.fit_transform(KNOWLEDGE_GRAPH, ENTITIES)
    print(EMBEDDINGS)
    print(cosine_similarity(EMBEDDINGS))

    
    
