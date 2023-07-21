"""
1st step of the pipeline: retrieve content related to events: description, types, embeddings
"""
# -*- coding: utf-8 -*-
import argparse
import pickle
from typing import List
import numpy as np
import pandas as pd
from tqdm import tqdm
from rdflib.namespace import OWL
from sentence_transformers import SentenceTransformer

from src.logger import Logger
from src.kg.hdt_kg import HDTKG
from src.kg.sparql_kg import SPARQLInterface
from settings import FRAMESTER_ENDPOINT, FOLDER_HDT_GEN_DB, FOLDER_HDT_GEN_DB_TYPES

class EventInfoRetrieval:
    """ Main class to retrieve info from events """
    def __init__(self, generic_kg: HDTKG, linguistic_kg: SPARQLInterface,
                 model_emb: str = 'sentence-transformers/bert-base-nli-mean-tokens'):
        self.generic_kg = generic_kg
        self.linguistic_kg = linguistic_kg
        self.model_emb = SentenceTransformer(model_emb)

        self.discarded_types = [str(OWL.Thing)]

    def get_description(self, node: str) -> str:
        """ Retrieve description of a node """
        return self.generic_kg.get_abstract(node=node)

    def get_types(self, node: str) -> List[str]:
        """ Retrieve node types: (node, rdf:type, ?t) """
        type_node = self.generic_kg.get_type_node(node=node)
        type_node.extend(self.linguistic_kg.get_type_node(node=node))
        return list(set(x for x in type_node if x not in self.discarded_types))

    @staticmethod
    def pre_process_text(text: str):
        """ Main pre-processing """
        return text.lower()

    def get_emb(self, text: str) -> np.ndarray:
        """ Embed text using transformers """
        return self.model_emb.encode(self.pre_process_text(text))

    def __call__(self, nodes: List[str], cached: dict):
        """ Main """
        res = {}
        for i in tqdm(range(len(nodes))):
            node = nodes[i]
            if node not in cached:
                info = {"description": self.get_description(node=node),
                        "types": self.get_types(node=node)}
                if info["description"]:
                    info.update({"description_embedding": self.get_emb(info["description"][0])})
                else:
                    info.update({"description_embedding": None})
                res[node] = info
        res.update(cached)
        return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-m', "--model", default='sentence-transformers/bert-base-nli-mean-tokens',
                    help="model to use for sentence transformers")
    ap.add_argument('-i', "--input", required=True,
                    help="csv path that contains the nodes to extract info from. Nodes should be in a 'entity' column")
    ap.add_argument('-o', "--output", required=True,
                    help="output path to save data")
    ap.add_argument('-c', "--cached", required=False,
                    help="optional - cached data (pkl file)")
    args_main = vars(ap.parse_args())

    CONFIG = {
        'rdf_type': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
        'abstract': 'http://dbpedia.org/ontology/abstract'
    }

    GENERIC_KG = HDTKG(folder_hdt=[FOLDER_HDT_GEN_DB, FOLDER_HDT_GEN_DB_TYPES],
                       nested_dataset=True, config=CONFIG)
    LINGUISTIC_KG = SPARQLInterface(sparql_endpoint=FRAMESTER_ENDPOINT)
    LOGGER = Logger()

    if args_main["cached"]:
        with open(args_main["cached"], encoding='utf-8') as openfile:
            CACHED = pickle.load(openfile)
    else:
        CACHED = {}

    EVENT_INFO_RETRIEVAL = EventInfoRetrieval(generic_kg=GENERIC_KG, linguistic_kg=LINGUISTIC_KG,
                                              model_emb=args_main["model"])
    NODES = pd.read_csv(args_main["input"]).entity.values

    LOGGER.log_start(name="Retrieving event info")
    RES = EVENT_INFO_RETRIEVAL(nodes=NODES, cached=CACHED)
    LOGGER.log_end()

    with open(args_main["output"], "wb") as openfile:
        pickle.dump(RES, openfile)
