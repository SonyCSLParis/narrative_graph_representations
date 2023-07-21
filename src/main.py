"""
Running all the steps of the pipeline.
"""
# -*- coding: utf-8 -*-
import os
import pickle
import argparse
import pandas as pd
from src.logger import Logger
from src.kg.hdt_kg import HDTKG
from src.kg.sparql_kg import SPARQLInterface
from src.prompt_srl import PromptSRL
from src.build_graph import GraphBuilder
from src.map_type_to_frame import MapKGs
from src.retrieve_frame_info import FrameInfoRetrieval
from src.retrieve_event_info import EventInfoRetrieval
from src.combine_event_frame_data import main_combine
from settings import FRAMESTER_ENDPOINT, FOLDER_HDT_GEN_DB, FOLDER_HDT_GEN_DB_TYPES

CONFIG = {
        'rdf_type': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
        'abstract': 'http://dbpedia.org/ontology/abstract'
    }

GENERIC_KG = HDTKG(folder_hdt=[FOLDER_HDT_GEN_DB, FOLDER_HDT_GEN_DB_TYPES],
                   nested_dataset=True, config=CONFIG)
LINGUISTIC_KG = SPARQLInterface(sparql_endpoint=FRAMESTER_ENDPOINT)

LOGGER = Logger()

def get_cached(args):
    """ Load cache or init empty dict """
    if args["cached"]:
        with open(args["cached"], encoding='utf-8') as openfile:
            return pickle.load(openfile)
    return {}

def main(args, cached):
    """ Run all steps """

    # 1 - Event Info Retrieval
    event_info_retrieval = EventInfoRetrieval(generic_kg=GENERIC_KG, linguistic_kg=LINGUISTIC_KG,
                                              model_emb=args["model"])
    df_ = nodes = pd.read_csv(args["input"])
    df_.to_csv(os.path.join(args["output"], "input.csv"))
    nodes = df_.entity.values

    LOGGER.log_start(name="Retrieving event info")
    events_info = event_info_retrieval(nodes=nodes, cached=cached)
    LOGGER.log_end()

    with open(os.path.join(args["output"], "events_info.pkl"), "wb") as openfile:
        pickle.dump(events_info, openfile)

    # 2 - Map KGs
    map_kgs = MapKGs(generic_kg=GENERIC_KG, linguistic_kg=LINGUISTIC_KG)
    event_types = list(set(t for _, x in events_info.items() for t in x["types"] ))

    LOGGER.log_start(name="Mapping event types to frames")
    map_info = map_kgs(nodes=event_types, cached=cached)
    LOGGER.log_end()

    with open(os.path.join(args["output"], "type_to_frame.pkl"), "wb") as openfile:
        pickle.dump(map_info, openfile)

    # 3 - Frame Info Retrieval
    frame_info_retrieval = FrameInfoRetrieval(linguistic_kg=LINGUISTIC_KG, model_emb=args["model"])
    frames = list(set(t for _, x in map_info.items() for t in x))

    LOGGER.log_start(name="Retrieving info from frames")
    frames_info = frame_info_retrieval(nodes=frames, cached=cached)
    LOGGER.log_end()

    with open(os.path.join(args["output"], "frames_info.pkl"), "wb") as openfile:
        pickle.dump(frames_info, openfile)

    # 4 - Combining info
    LOGGER.log_start(name="Combine event and frame info")
    events_info = main_combine(events_info, map_info, frames_info)
    LOGGER.log_end()

    with open(os.path.join(args["output"], "events_info_combined.pkl"), "wb") as openfile:
        pickle.dump(events_info, openfile)

    # 5 - Prompting
    prompt_srl = PromptSRL()
    LOGGER.log_start(name="Prompt SRL + GPT")
    events_info = prompt_srl(events_info=events_info)
    LOGGER.log_end()

    with open(os.path.join(args["output"], "events_info_combined_srl.pkl"), "wb") as openfile:
        pickle.dump(events_info, openfile)

    # 6 - Graph building
    graph_builder = GraphBuilder()
    LOGGER.log_start(name="Prompt SRL + GPT")
    graph = graph_builder(events_info=events_info)
    LOGGER.log_end()

    graph.serialize(destination=os.path.join(args["output"], "kg.ttl"), format="turtle")


if __name__ == '__main__':
    # Run all steps of the pipeline
    ap = argparse.ArgumentParser()
    ap.add_argument('-m', "--model", default='sentence-transformers/bert-base-nli-mean-tokens',
                    help="model to use for sentence transformers")
    ap.add_argument('-i', "--input", required=True,
                    help="csv path that contains the nodes to extract info from." + \
                         "Nodes should be in a 'entity' column")
    ap.add_argument('-o', "--output", required=True,
                    help="output folder to save data")
    ap.add_argument('-c', "--cached", required=False,
                    help="optional - cached data (pkl file)")
    args_main = vars(ap.parse_args())

    if not os.path.exists(args_main["output"]):
        os.makedirs(args_main["output"])

    CACHED = get_cached(args=args_main)
    main(args_main, CACHED)
    