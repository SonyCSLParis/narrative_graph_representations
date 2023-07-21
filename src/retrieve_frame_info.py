"""
3rd step of the pipeline: retrieve content related to frames: frame elements, description, embedding
"""
# -*- coding: utf-8 -*-
import argparse
import pickle
import numpy as np
from typing import List
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from src.logger import Logger
from src.kg.sparql_kg import SPARQLInterface
from settings import FRAMESTER_ENDPOINT

class FrameInfoRetrieval:
    """ Main class to retrieve info from frames """
    def __init__(self, linguistic_kg: SPARQLInterface,
                 model_emb: str = 'sentence-transformers/bert-base-nli-mean-tokens'):
        self.linguistic_kg = linguistic_kg
        self.model_emb = SentenceTransformer(model_emb)

    def get_comment(self, node):
        """ Retrieve comment (description of frame) """
        return self.linguistic_kg.get_comment_node(node)

    def get_frame_element(self, node):
        """ Retrieve frame elements """
        return self.linguistic_kg.get_frame_elements(frame=node)

    @staticmethod
    def pre_process_text(text: str):
        """ Main pre-processing """
        return text.lower()

    def get_emb(self, text: str) -> np.ndarray:
        """ Embed text using transformers """
        return self.model_emb.encode(self.pre_process_text(text))

    def __call__(self, nodes: List[str], cached: dict):
        """ Main 
        nodes: frames
        """
        res = {}
        for i in tqdm(range(len(nodes))):
            node = nodes[i]
            if node not in cached:
                info = {"description": self.get_comment(node=node),
                        "frame_elements": self.get_frame_element(node=node)}
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
                    help="pkl path that contains the mapping type/frame " + \
                         "Can be computed with `map_type_to_frame.py` script.")
    ap.add_argument('-o', "--output", required=True,
                    help="output path to save data")
    ap.add_argument('-c', "--cached", required=False,
                    help="optional - cached data (pkl file)")
    args_main = vars(ap.parse_args())

    CONFIG = {
        'rdf_type': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
        'abstract': 'http://dbpedia.org/ontology/abstract'
    }

    LINGUISTIC_KG = SPARQLInterface(sparql_endpoint=FRAMESTER_ENDPOINT)
    LOGGER = Logger()

    if args_main["cached"]:
        with open(args_main["cached"], encoding='utf-8') as openfile:
            CACHED = pickle.load(openfile)
    else:
        CACHED = {}

    FRAME_INFO_RETRIEVAL = FrameInfoRetrieval(linguistic_kg=LINGUISTIC_KG,
                                              model_emb=args_main["model"])
    with open(args_main["input"], 'rb') as openfile:
        INFO = pickle.load(openfile)
    FRAMES = list(set(t for _, x in INFO.items() for t in x))

    LOGGER.log_start(name="Retrieving info from frames")
    RES = FRAME_INFO_RETRIEVAL(nodes=FRAMES, cached=CACHED)
    LOGGER.log_end()

    with open(args_main["output"], "wb") as openfile:
        pickle.dump(RES, openfile)
