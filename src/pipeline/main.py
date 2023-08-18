"""
Running all the steps of the pipeline.
"""
# -*- coding: utf-8 -*-
import os
import pickle
import argparse
import subprocess
from datetime import datetime
import pandas as pd
from src.logger import Logger
from src.kg.hdt_kg import HDTKG
from src.kg.sparql_kg import SPARQLInterface
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


def main(args):
    """ Run all steps, to be run from root directory """
    start = datetime.now()

    df_ = pd.read_csv(args["input"])
    df_.to_csv(os.path.join(args["output"], "input.csv"))

    # 1 - Event Info Retrieval
    output_f = os.path.join(args["output"], "events_info.pkl")
    command = f"""
    python src/pipeline/retrieve_event_info.py -m {args["model"]} \
        -i {args["input"]} -o {output_f}
    """
    subprocess.call(command, shell=True)

    # 2 - Map KGs
    input_f = os.path.join(args["output"], "events_info.pkl")
    output_f = os.path.join(args["output"], "type_to_frame.pkl")
    command = f"""
    python src/pipeline/map_type_to_frame.py -i {input_f} \
        -o {output_f}
    """
    subprocess.call(command, shell=True)

    # 3 - Frame Info Retrieval
    input_f = os.path.join(args["output"], "type_to_frame.pkl")
    output_f = os.path.join(args["output"], "frames_info.pkl")
    command = f"""
    python src/pipeline/retrieve_frame_info.py -m {args["model"]} \
        -i {input_f} -o {output_f}
    """
    subprocess.call(command, shell=True)

    # 4 - Combining info
    command = f"""
    python src/pipeline/combine_event_frame_data.py \
        -e {os.path.join(args["output"], "events_info.pkl")} \
        -m {os.path.join(args["output"], "type_to_frame.pkl")} \
        -f {os.path.join(args["output"], "frames_info.pkl")} \
        -o {os.path.join(args["output"], "events_info_combined.pkl")}
    """
    subprocess.call(command, shell=True)

    # 5 - Prompting
    input_f = os.path.join(args["output"], "events_info_combined.pkl")
    output_f = os.path.join(args["output"], "events_info_combined_srl.pkl")
    command = f"""
    python src/pipeline/prompt_srl.py -e {input_f} \
        -o {output_f}
    """
    subprocess.call(command, shell=True)

    # 6 - Enriching SRL Info (DBpedia Spotlight)
    input_f = os.path.join(args["output"], "events_info_combined_srl.pkl")
    output_f = os.path.join(args["output"], "events_info_final.pkl")
    command = f"""
    python src/pipeline/enrich_srl.py -e {input_f} \
        -o {output_f}
    """
    subprocess.call(command, shell=True)

    # 7 - Graph building
    input_f = os.path.join(args["output"], "events_info_final.pkl")
    output_f = os.path.join(args["output"], "kg.ttl")
    command = f"""
    python src/pipeline/build_graph.py -e {input_f} \
        -o {output_f}
    """
    subprocess.call(command, shell=True)

    end = datetime.now()
    print(f"Took {end-start}")


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
    # ap.add_argument('-c', "--cached", required=False,
    #                 help="optional - cached data (pkl file)")
    args_main = vars(ap.parse_args())

    if not os.path.exists(args_main["output"]):
        os.makedirs(args_main["output"])

    # CACHED = get_cached(args=args_main)
    main(args_main)
    