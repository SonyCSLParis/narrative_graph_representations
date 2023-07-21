"""
2nd step of the pipeline: map (event) node types to frames in framester
"""
# -*- coding: utf-8 -*-
import argparse
import pickle
from typing import List
from tqdm import tqdm
from src.logger import Logger
from src.kg.hdt_kg import HDTKG
from src.kg.sparql_kg import SPARQLInterface
from settings import FRAMESTER_ENDPOINT, FOLDER_HDT_GEN_DB, FOLDER_HDT_GEN_DB_TYPES

class MapKGs:
    """ Mapping information from KGs """
    def __init__(self, generic_kg: HDTKG, linguistic_kg: SPARQLInterface):
        self.generic_kg = generic_kg
        self.linguistic_kg = linguistic_kg

    def __call__(self, nodes: List[str], cached: dict):
        """ Main mapping 
        - nodes: event types """
        res = {}
        for i in tqdm(range(len(nodes))):
            node = nodes[i]
            if node not in cached:
                eq_class_yago = self.generic_kg.get_equivalent_class_yago(node)
                res[node] = self.linguistic_kg.get_frames([(node, eq_class_yago)])
        res.update(cached)
        return res

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', "--input", required=True,
                    help="pkl path that contains the event info. " + \
                         "Can be computed with `retrieve_event.py` script.")
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

    MAP_KGS = MapKGs(generic_kg=GENERIC_KG, linguistic_kg=LINGUISTIC_KG)

    with open(args_main["input"], 'rb') as openfile:
        INFO = pickle.load(openfile)
    EVENT_TYPES = list(set(t for _, x in INFO.items() for t in x["types"] ))

    LOGGER.log_start(name="Mapping event types to frames")
    RES = MAP_KGS(nodes=EVENT_TYPES, cached=CACHED)
    LOGGER.log_end()

    with open(args_main["output"], "wb") as openfile:
        pickle.dump(RES, openfile)
