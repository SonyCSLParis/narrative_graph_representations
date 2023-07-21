"""
4th step of the pipeline: Add info related to frames in event info
"""
# -*- coding: utf-8 -*-
import argparse
from types import NoneType
import torch
import pickle
from tqdm import tqdm
import numpy as np
from sentence_transformers import util

from src.logger import Logger

def main_combine(events_info: dict, map_info: dict, frame_info: dict) -> dict:
    """ Main """
    events = list(events_info.keys())

    for i in tqdm(range(len(events))):
        # Add frames
        event = events[i]
        events_info[event]["frames"] = list(set(x for type_ in events_info[event]["types"] \
            for x in map_info[type_]))
        events_info[event]["frames_with_des"] = [frame \
            for frame in events_info[event]["frames"] \
                if not isinstance(frame_info[frame]["description_embedding"], NoneType)]

        # Add frame similarity
        if events_info[event]["frames_with_des"] and not isinstance(events_info[event]['description_embedding'], NoneType):
            emb_event = events_info[event]['description_embedding']
            emb_frames = np.stack([frame_info[frame]['description_embedding'] \
                for frame in events_info[event]["frames_with_des"]])
            similarities = util.pytorch_cos_sim(emb_event, emb_frames)
            events_info[event]["frames_similarity"] = similarities

            # Add most similar frame info
            name = events_info[event]["frames_with_des"][int(torch.argmax(similarities))]
            most_similar = {
                'name': name, 'score': float(torch.max(similarities)),
                'frame_elements': frame_info[name]["frame_elements"]
            }
            events_info[event]["most_similar_frame"] = most_similar

    return events_info


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-e', "--events_info", required=True,
                    help="events_info, cf `retrieve_events_info.py`")
    ap.add_argument('-m', "--map_info", required=True,
                    help="map_info, cf `map_type_to_frame.py`")
    ap.add_argument('-f', "--frame_info", required=True,
                    help="frame_info, cf `retrieve_frame_info.py`")
    ap.add_argument('-o', "--output", required=True,
                    help="output path to save data")
    args_main = vars(ap.parse_args())
    
    with open(args_main["events_info"], "rb") as openfile:
        EVENTS_INFO = pickle.load(openfile)

    with open(args_main["map_info"], "rb") as openfile:
        MAP_INFO = pickle.load(openfile)

    with open(args_main["frame_info"], "rb") as openfile:
        FRAME_INFO = pickle.load(openfile)
    
    LOGGER = Logger()

    LOGGER.log_start(name="Combine event and frame info")
    RES = main_combine(EVENTS_INFO, MAP_INFO, FRAME_INFO)
    LOGGER.log_end()

    with open(args_main["output"], "wb") as openfile:
        pickle.dump(RES, openfile)

