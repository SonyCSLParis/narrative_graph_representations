"""
Embedding-based methods to choose most meaningful frames for an event
"""
# -*- coding: utf-8 -*-
import os
import pickle
from tqdm import tqdm
from typing import List, Tuple

import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util

from settings import FOLDER_PATH

class EmbedderSimilarity:
    """ Comparing event to frames with embeddings """

    def __init__(self, type_embedder: str):
        """
        type_embedder:
        -  `label`: using label from IRI to compare event and frames
        - `description`: using descriptions to compare event and frames
            * In DBpedia (?event, dbo:abstract, ?description)
            [* Not used, DBpedia+Framester: (?event, rdfs:comment, ?description)]
            * In Framester (?frame, rdfs:comment, ?description)
        - `graph_embedding`: using graph embeddings from Framester

        model
        - if type_embedder is `label`or `description`: 
        sentence-transformer (huggingface) model to use
        - if type_embedder is `graph_embedding`: 
        path to model
        """
        args = {"type_embedder": type_embedder}
        self._check_args(**args)
        self.type_embedder = type_embedder

        self.model = None

        # cache is a dict: key = iri, value = embedding
        self.save_cache_file = os.path.join(FOLDER_PATH, f"cached/{type_embedder}.pkl")
        if os.path.exists(self.save_cache_file):
            with open(self.save_cache_file, "rb") as openfile:
                self.cache = pickle.load(openfile)
        else:
            self.cache = {}

    def _check_args(self, **args):
        types = ["label", "description", "graph_embedding"]
        if args["type_embedder"] not in types:
            raise ValueError(f"arg `type_embedder` should be in {types}")


class TextEmbedding(EmbedderSimilarity):
    """ Using text input to compare events and frames """
    def __init__(self, type_embedder: str, model: str = 'sentence-transformers/bert-base-nli-mean-tokens'):
        EmbedderSimilarity.__init__(self, type_embedder=type_embedder)
        self.model = SentenceTransformer(model)

    @staticmethod
    def pre_process_label(iri: str):
        """ Keeping only readable label """
        return iri.rsplit("/", maxsplit=1)[-1].replace('_', ' ')

    @staticmethod
    def pre_process_text(text: str):
        """ Main pre-processing """
        return text.lower()

    def get_encoding(self, iri: str, content: str):
        """ Retrieving encoding, either from cache or direct computation """
        if iri not in self.cache:
            self.cache[iri] = self.model.encode(content)
        return self.cache[iri]

    def save_cache(self):
        """ Saving cache as pickle dictionary """
        with open(self.save_cache_file, 'wb') as openfile:
            pickle.dump(self.cache, openfile)

    def compare(self, event: Tuple[str, str], frames: List[Tuple[str, str]]):
        """ Main
        event: (iri of event, label/description)
        frames: list of (iri of event, label/description) """
        emb_event = self.get_encoding(iri=event[0], content=self.pre_process_text(event[1]))
        emb_frames = [self.get_encoding(iri=frame[0], content=self.pre_process_text(frame[1])) \
            for frame in frames]
        emb_frames = np.stack(emb_frames)
        similarities = util.pytorch_cos_sim(emb_event, emb_frames)

        self.save_cache()
        return similarities
    
    def embed(self, nodes: List[Tuple[str, str]]):
        """ Embedding and caching nodes content """
        for i in tqdm(range(len(nodes))):
            node = nodes[i]
            self.get_encoding(iri=node[0], content=self.pre_process_text(node[1]))
        self.save_cache()

    @staticmethod
    def get_most_similar_frame(similarities):
        """ Most similar frame + index """
        return float(torch.max(similarities)), int(torch.argmax(similarities))



class GraphEmbedding(EmbedderSimilarity):
    """ Using graph input to compare events and frames """
    def __init__(self, type_embedder: str, model: str):
        EmbedderSimilarity.__init__(self, type_embedder=type_embedder)


if __name__ == '__main__':
    EMBEDDER_SIMILARITY = TextEmbedding(
        type_embedder="label",
        model='sentence-transformers/bert-base-nli-mean-tokens')

    EVENT = ("http://dbpedia.org/resource/Coup_of_18_Fructidor", "Coup of 18 Fructidor")

    FRAMES = [
        'https://w3id.org/framester/framenet/abox/frame/Change_of_leadership',
        'https://w3id.org/framester/framenet/abox/frame/Intentionally_act',
        'https://w3id.org/framester/framenet/abox/frame/Commonality',
        'https://w3id.org/framester/framenet/abox/frame/Event'
    ]
    FRAMES = [(frame, frame.rsplit("/", maxsplit=1)[-1].replace('_', ' ')) for frame in FRAMES]
    SIMILARITIES = EMBEDDER_SIMILARITY.compare(EVENT, FRAMES)
    SIM, INDEX = EMBEDDER_SIMILARITY.get_most_similar_frame(similarities=SIMILARITIES)
    print(f"With labels\n{SIM}\t{INDEX}\t{FRAMES[INDEX][0]}\n===")

    ############################################################################################

    EVENT = ( \
        "http://dbpedia.org/resource/Coup_of_18_Fructidor", \
        "The Coup of 18 Fructidor, Year V (4 September 1797 in the French Republican Calendar), was a seizure of power in France by members of the Directory, the government of the French First Republic, with support from the French military. The coup was provoked by the results of elections held months earlier, which had given the majority of seats in the country's Corps législatif (Legislative body) to royalist candidates, threatening a restoration of the monarchy and a return to the ancien régime. Three of the five members of the Directory, Paul Barras, Jean-François Rewbell and Louis Marie de La Révellière-Lépeaux, with support of foreign minister Charles Maurice de Talleyrand-Périgord, staged the coup d'état that annulled many of the previous election's results and ousted the monarchists from the legislature.")

    FRAMES = [
        ('https://w3id.org/framester/framenet/abox/frame/Change_of_leadership', \
         "This frame concerns the appointment of a New_leader or removal from office of an Old_leader. The Selector brings about the change in leadership, for example, by electing or overthrowing a leader. Some words in the frame describe the successful removal from office of a leader (e.g. depose, oust), others simply the attempt (e.g. uprising, rebellion). On March 17 , Mamedov appointed Rakhim Gasiyev as Defence Minister"),
        ('https://w3id.org/framester/framenet/abox/frame/Intentionally_act', \
         'This is an abstract frame for acts performed by sentient beings. It exists mostly for FE inheritance. I carried out the deed easily .'),
        ('https://w3id.org/framester/framenet/abox/frame/Commonality', \
         'This frame contains words that describe a set of individuals which possess some Commonality, generally a common attribute. Their common enemy was Britain.'), 
        ('https://w3id.org/framester/framenet/abox/frame/Event', \
         'An Event takes place at a Place and Time. Big earthquakes only happen along plate boundaries. INI The party will take place on Sunday in the all-you-can-eat buffet.')
    ]
    EMBEDDER_SIMILARITY = TextEmbedding(
        type_embedder="description",
        model='sentence-transformers/bert-base-nli-mean-tokens')
    SIMILARITIES = EMBEDDER_SIMILARITY.compare(EVENT, FRAMES)
    SIM, INDEX = EMBEDDER_SIMILARITY.get_most_similar_frame(similarities=SIMILARITIES)
    print(f"With descriptions\n{SIM}\t{INDEX}\t{FRAMES[INDEX][0]}\n===")
