"""
Analyse output of pipeline
"""
# -*- coding: utf-8 -*-
import argparse
import pickle
from collections import Counter, defaultdict
import pandas as pd
import numpy as np

def describe_gen(data, key: str, label: str, top_n: int = 5):
    """ statistics about events """
    types = [v[key] for _, v in data.items()]
    print(f"Avg number of event {label}: {np.mean([len(x) for x in types])}")
    print(f"# of events with no {label}: {len([x for x in types if not x])}")

    count = Counter([x for elt in types for x in elt])
    print(f"Top {top_n} classes in {label}:")
    for (iri, nb_) in count.most_common(top_n):
        print(f"- {iri}: {nb_}")


def describe_ms_frame(ms_frames, ms_sim, ms_fe, top_n = 5):
    """ most similar frames statistics """
    print(f"Top {top_n} most similar frames:")
    for (iri, nb_) in ms_frames.most_common(top_n):
        print(f"- {iri}: {nb_}")

    print(f"Avg similarity score: {round(np.mean(ms_sim), 2)}")
    print(f"Min/Max similarity score: {round(np.min(ms_sim), 2)}/{round(np.max(ms_sim), 2)}")
    print(f"Avg # frame elements: {round(np.mean(ms_fe), 1)}")


def get_srl_info(event_info):
    """ srl stats """
    df_ = event_info["srl"].fillna("")
    df_["gpt_ds_iri"] = df_.apply(merge_gpt_ds_iri, axis=1)
    res = df_.groupby("type_fes").agg({
        "role_text": ["count", lambda x: \
            x[(~x.str.contains('unknown')) & (~x.str.contains('ot mentioned in the text'))] \
                .count()],
        "role_iri": [lambda x: x[~x.str.contains('unknown')].count()],
        "ds_iri": [lambda x: x[~x.isin([''])].count()],
        "gpt_ds_iri": [lambda x: x[~x.isin([0])].count()]})
    res.columns = ['nb_fe', 'nb_fe_filled_text', 'nb_fe_filled_iri_gpt',
                   'nb_fe_filled_iri_ds', 'nb_fe_filled_iri_gpt_ds']
    res = res.to_dict(orient='tight')
    return [(label, res['data'][i]) for i, label in enumerate(res["index"])]


def merge_gpt_ds_iri(row):
    """ merging results from gpt and spotlight """
    res = []
    if (row['role_iri'] != "<unknown>") and \
        isinstance(row['role_iri'], str):  # mapped to a DBpedia IRI
        res += [x for x in row['role_iri'].split(", ") if x.startswith("http")]
    res += [x for x in row["ds_iri"].split("\t") if x]
    return len(res)


def group_srl(srl_info):
    """ group info per type of frame element (core etc) """
    res = defaultdict(list)
    for elt in srl_info:
        for (type_fe, nbs) in elt:
            for i, nb_ in enumerate(nbs):
                res[f"{type_fe}_{i}"].append(nb_)
    return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', "--input", required=True,
                    help="events_info, output of the pipeline")
    args_main = vars(ap.parse_args())


    with open(args_main["input"], "rb") as openfile:
        DATA = pickle.load(openfile)

    NB_EVENTS = len(DATA)
    print(f"Number of events: {NB_EVENTS}")
    NB_EVENTS_WITH_DES = len({k for k, v in DATA.items() if v["description"]})
    print(f"Number of events with descriptions: {NB_EVENTS_WITH_DES} " + \
        f"({round(100*NB_EVENTS_WITH_DES/NB_EVENTS, 1)}%)")

    describe_gen(DATA, "types", "types")
    describe_gen(DATA, "frames", "frames")

    MOST_SIMILAR = {k: v for k, v in DATA.items() \
        if v.get('most_similar_frame') and not isinstance(v.get('srl'), str)}
    print(f"# of events with frames+descriptions: {len(MOST_SIMILAR)}")

    MS_FRAMES = Counter([v["most_similar_frame"]["name"] for _, v in MOST_SIMILAR.items()])
    MS_SIM = [v["most_similar_frame"]["score"] for _, v in MOST_SIMILAR.items()]
    MS_FE = [len(v["most_similar_frame"]["frame_elements"]) for _, v in MOST_SIMILAR.items()]
    describe_ms_frame(MS_FRAMES, MS_SIM, MS_FE)

    SUBSET_WITH_DF = {k: v for k, v in MOST_SIMILAR.items() if isinstance(v['srl'], pd.DataFrame)}
    SRL = [get_srl_info(event_info) for _, event_info in SUBSET_WITH_DF.items()]
    RES = group_srl(srl_info=SRL)

    print("===============")
    # 0: fe, 1: fe with text, 2: fe with iri
    print(RES)
    print(RES[0])
    print(len(RES))
    for k, v in RES.items():
        if v:
            print(f"{k}\t{round(np.mean(v), 2)}")
    print("===============\n")
