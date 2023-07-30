"""
7th step of the pipeline: build the graph from info
"""
# -*- coding: utf-8 -*-
import argparse
import pickle
import pandas as pd
from rdflib import Namespace, Graph, URIRef
from rdflib.namespace import RDF 
from src.logger import Logger

class GraphBuilder:
    """ Build graph from frame information """
    def __init__(self, base_prefix: str = "http://example.org/muhai/narratives#"):
        self.base_prefix = base_prefix
        self.dul = Namespace("http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#")
        self.rdf = RDF
        self.fe_prefix = "https://w3id.org/framester/framenet/abox/fe"

    @staticmethod
    def get_unique_descriptions(events_info):
        """ UNique descriptions from most similar frames """
        res = {}
        for _, info in events_info.items():
            if info.get('most_similar_frame'):
                name = info['most_similar_frame']["name"]
                if name not in res:
                    res[name] = {'frame_elements': info['most_similar_frame']["frame_elements"]}
        return res

    def add_descriptions(self, graph, descriptions_info):
        """ Add descriptions into graph: frame is a description, frame elements
        entities, linked to their description with (?frame, dul:describes, ?fe_)"""
        for des, info in descriptions_info.items():
            graph.add((URIRef(des), self.rdf.type, self.dul.Description))
            for fe_ in info['frame_elements']:
                graph.add((URIRef(fe_), self.rdf.type, self.dul.Entity))
                graph.add((URIRef(des), self.dul.describes, URIRef(fe_)))
        return graph

    def add_situations(self, graph, events_info):
        """ Add situations into graph: for each event that was linked to a frame """
        for event, info in events_info.items():
            if info.get("most_similar_frame"):
                frame = info['most_similar_frame']['name']
                graph.add((URIRef(event), self.rdf.type, self.dul.Situation))
                graph.add((URIRef(event), self.dul.satisfies, URIRef(frame)))

                if isinstance(info['srl'], pd.DataFrame):
                    for _, row in info['srl'].iterrows():
                        if (row['role iri'] != "<unknown>") and isinstance(row['role iri'], str):  # mapped to a DBpedia IRI
                            roles = [x for x in row['role iri'].split(", ") if x.startswith("http")]
                            for role in roles:
                                role_iri = role.replace("<", "").replace(">", "")
                                graph.add((URIRef(role_iri), self.dul.hasSetting, URIRef(event)))
                                fe_ = self.get_iri_frame_element(label=row['role name'], frame_name=frame)
                                graph.add((URIRef(role_iri), self.dul.associatedWith, URIRef(fe_)))

        return graph

    def init_graph(self):
        """ Init KG: bind namespaces """
        graph = Graph()
        graph.bind("dul", self.dul)
        graph.bind("rdf", self.rdf)
        return graph

    def get_iri_frame_element(self, label, frame_name):
        """ Reverse engineer: from frame element label to uri """
        frame_name = frame_name.split("/")[-1].lower()
        return f"{self.fe_prefix}/{label.replace(' ', '_')}.{frame_name}"

    def __call__(self, events_info):
        """ events_info: cf output of prompt_srl.py """
        graph = self.init_graph()

        # Descriptions
        unique_des = self.get_unique_descriptions(events_info=events_info)
        graph = self.add_descriptions(graph=graph, descriptions_info=unique_des)

        # Situations
        graph = self.add_situations(graph=graph, events_info=events_info)

        return graph


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-e', "--events_info", required=True,
                    help="events_info, cf `prompt_srl.py`")
    ap.add_argument('-o', "--output", required=True,
                    help="output path to save data")
    args_main = vars(ap.parse_args())

    with open(args_main["events_info"], "rb") as openfile:
        EVENTS_INFO = pickle.load(openfile)

    GRAPH_BUILDER = GraphBuilder()
    LOGGER = Logger()

    LOGGER.log_start(name="Building graph")
    RES = GRAPH_BUILDER(events_info=EVENTS_INFO)
    LOGGER.log_end()

    RES.serialize(destination=args_main["output"], format="turtle")
