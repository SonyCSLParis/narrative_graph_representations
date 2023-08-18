"""
6th step of the pipeline: enrich info retrieved with ChatGPT
"""
# -*- coding: utf-8 -*-
import argparse
import pickle
from tqdm import tqdm
import spacy
import pandas as pd
from src.logger import Logger

class EnrichSRL:
    """ Using NLP tools to enrich semantic roles extracted with LLM """
    def __init__(self, model: str = "en_core_web_sm"):
        """
        Install dbpedia spotlight extension in spacy, follow instructions here:
        https://github.com/MartinoMensio/spacy-dbpedia-spotlight

        In dbpedia-desktop folder with .jar and model, run
        java -Xmx8G -jar rest-1.1-jar-with-dependencies.jar en http://localhost:2222/rest
        """
        self.nlp = spacy.load(model)
        self.nlp.add_pipe(
            "dbpedia_spotlight",
            config={'confidence': 0.7,
                    'dbpedia_rest_endpoint': 'http://localhost:2222/rest'})

    @staticmethod
    def ents_to_uri(ents: tuple) -> str:
        """ From entity return DBpedia URI """
        res = []
        for ent in ents:
            if ent._.dbpedia_raw_result:
                res.append(ent._.dbpedia_raw_result.get("@URI"))
        return "\t".join(res)

    @staticmethod
    def update_role_text(text: str) -> str:
        """ Ensuring no value from role text column is empty """
        return text if text else "<unknown>"

    def __call__(self, events_info: dict) -> dict:
        """ Main """
        for (_, event_info) in tqdm(events_info.items()):
            if isinstance(event_info['srl'], pd.DataFrame):
                # Spacy + DBpedia Spotlight
                event_info['srl'].columns = \
                    ['role_name', 'role_iri', 'role_text', 'role_name_iri', 'type_fes']
                event_info['srl'] = event_info['srl'].fillna("")
                event_info['srl']['role_text'] = \
                    event_info['srl']['role_text'].apply(self.update_role_text)

                docs = self.nlp.pipe(event_info['srl']['role_text'].values, n_process=4)
                docs = list(docs)
                event_info['srl']['ds_iri'] = [self.ents_to_uri(doc.ents) for doc in docs]
        return events_info


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-e', "--events_info", required=True,
                    help="events_info, cf `prompt_srl.py`")
    ap.add_argument('-o', "--output", required=True,
                    help="output path to save data")
    args_main = vars(ap.parse_args())

    with open(args_main["events_info"], "rb") as openfile:
        EVENTS_INFO = pickle.load(openfile)

    ENRICH_SRL = EnrichSRL()
    LOGGER = Logger()

    LOGGER.log_start(name="Enrich SRL post GPT")
    RES = ENRICH_SRL(events_info=EVENTS_INFO)
    LOGGER.log_end()

    with open(args_main["output"], "wb") as openfile:
        pickle.dump(RES, openfile)
