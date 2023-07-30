"""
Analyse output of pipeline
"""
# -*- coding: utf-8 -*-
import os
import pickle
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
from settings import FOLDER_PATH


# with open(os.path.join(FOLDER_PATH, "data/ex-full-pipeline/event_info_combined_srl.pkl"), "rb") as openfile:
#     data = pickle.load(openfile)
with open(os.path.join(FOLDER_PATH, "data/2023-07-24_example-all/events_info_final.pkl"), "rb") as openfile:
    data = pickle.load(openfile)


def describe_gen(data, key: str, label: str, top_n: int = 5):
    types = [v[key] for _, v in data.items()]
    print(f"Avg number of event {label}: {np.mean([len(x) for x in types])}")
    print(f"# of events with no {label}: {len([x for x in types if not x])}")

    count = Counter([x for elt in types for x in elt])
    print(f"Top {top_n} classes in {label}:")
    for (iri, nb) in count.most_common(top_n):
        print(f"- {iri}: {nb}")

def describe_ms_frame(ms_frames, ms_sim, ms_fe, top_n = 5):
    print(f"Top {top_n} most similar frames:")
    for (iri, nb) in ms_frames.most_common(top_n):
        print(f"- {iri}: {nb}")
    
    print(f"Avg similarity score: {round(np.mean(ms_sim), 2)}")
    print(f"Min/Max similarity score: {round(np.min(ms_sim), 2)}/{round(np.max(ms_sim), 2)}")
    print(f"Avg # frame elements: {round(np.mean(ms_fe), 1)}")

def get_srl_info(event_info):
    df = event_info["srl"].fillna("")
    res = df.groupby("type_fes").agg({
        "role text": ["count", lambda x: x[~x.str.contains('<unknown>')].count()],
        "role iri": [lambda x: x[~x.str.contains('<unknown>')].count()],
        "ds_iri": [lambda x: x[~x.isin([''])].count()]})
    res.columns = ['nb_fe', 'nb_fe_filled_text', 'nb_fe_filled_iri_gpt', 'nb_fe_filled_iri_ds']
    res = res.to_dict(orient='tight')
    return ([(label, res['data'][i]) for i, label in enumerate(res["index"])])

def group_srl(srl_info):
    res = defaultdict(list)
    for x in srl_info:
        for (type_fe, nbs) in x:
            for i, nb in enumerate(nbs):
                res[f"{type_fe}_{i}"].append(nb)
    return res

nb_events = len(data)
print(f"Number of events: {nb_events}")
nb_events_with_des = len({k for k, v in data.items() if v["description"]})
print(f"Number of events with descriptions: {nb_events_with_des} " + \
    f"({round(100*nb_events_with_des/nb_events, 1)}%)")

describe_gen(data, "types", "types")
describe_gen(data, "frames", "frames")

most_similar = {k: v for k, v in data.items() \
    if v.get('most_similar_frame') and not isinstance(v.get('srl'), str)}
print(f"# of events with frames+descriptions: {len(most_similar)}")

ms_frames = Counter([v["most_similar_frame"]["name"] for _, v in most_similar.items()])
ms_sim = [v["most_similar_frame"]["score"] for _, v in most_similar.items()]
ms_fe = [len(v["most_similar_frame"]["frame_elements"]) for _, v in most_similar.items()]
describe_ms_frame(ms_frames, ms_sim, ms_fe)

subset_with_df = {k: v for k, v in most_similar.items() if isinstance(v['srl'], pd.DataFrame)}
srl = [get_srl_info(event_info) for _, event_info in subset_with_df.items()]
res = group_srl(srl_info=srl)

# 0: fe, 1: fe with text, 2: fe with iri
for k, v in res.items():
    print(f"{k}\t{np.mean(v)}")