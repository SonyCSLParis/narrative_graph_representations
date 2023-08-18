"""
7th step of the pipeline: build the graph from info
"""
# -*- coding: utf-8 -*-
import argparse
import pickle
from typing import Dict, List
import pandas as pd
from pandas.core.series import Series
from rdflib import Namespace, Graph, URIRef
from rdflib.namespace import RDF
from src.logger import Logger

class GraphBuilder:
    """ Build graph from frame information """
    # def __init__(self, mapping_fe_subclass_path: str,
    #              base_prefix: str = "http://example.org/muhai/narratives#"):
    def __init__(self,
                 base_prefix: str = "http://example.org/muhai/narratives#"):
        self.base_prefix = base_prefix
        self.dul = Namespace("http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#")
        self.rdf = RDF
        self.fe_prefix = "https://w3id.org/framester/framenet/abox/fe"
        self.premon = Namespace("http://premon.fbk.eu/resource/")

        # fe_subclass_df = pd.read_csv(mapping_fe_subclass_path)

        # self.fe_dul_mapping = defaultdict(list)
        # for _, row in fe_subclass_df.iterrows():
        #     self.fe_dul_mapping[row["fe"]].append(row["subclass"])

    @staticmethod
    def get_unique_descriptions(events_info: Dict) -> Dict:
        """ UNique descriptions from most similar frames """
        res = {}
        for _, info in events_info.items():
            if info.get('most_similar_frame'):
                name = info['most_similar_frame']["name"]
                if name not in res:
                    res[name] = {'frame_elements': info['most_similar_frame']["frame_elements"]}
        return res

    def add_descriptions(self, graph: Graph, descriptions_info: Dict) -> Graph:
        """ Add descriptions into graph: frame is a description, frame elements
        entities, linked to their description with (?frame, dul:describes, ?fe_)"""
        for des, info in descriptions_info.items():
            graph.add((URIRef(des), self.rdf.type, self.dul.Description))
            for fe_ in info['frame_elements']:
                graph.add((URIRef(fe_), self.rdf.type, self.dul.Role))
                graph.add((URIRef(des), self.dul.definesRole, URIRef(fe_)))
        return graph

    @staticmethod
    def get_roles(row: Series) -> List:
        """ Retrieving role fillers from row, both from GPT IRIs and DBpedia Spotlight IRIs"""
        res = []
        if (row['role_iri'] != "<unknown>") and \
            isinstance(row['role_iri'], str):  # mapped to a DBpedia IRI
            res += [x for x in row['role_iri'].split(", ") if x.startswith("http")]
        res += [x for x in row["ds_iri"].split("\t") if x]
        return res

    def add_roles_in_graph(self, row: Series, graph: Graph, frame: str, event: str) -> Graph:
        """ Adding roles in graph """
        roles = self.get_roles(row=row)
        for role in roles:
            role_iri = role.replace("<", "").replace(">", "")
            graph.add((URIRef(role_iri), self.dul.hasSetting, URIRef(event)))
            fe_ = self.get_iri_frame_element(
                label=row['role_name'], frame_name=frame)
            graph.add((URIRef(fe_), self.dul.classifies, URIRef(role_iri)))

            # for c_dul in [x for x in self.fe_dul_mapping[fe_] if x != str(self.dul.Description)]:
            #     graph.add((URIRef(role_iri), self.rdf.type, URIRef(c_dul)))
        return graph

    def add_situations(self, graph: Graph, events_info: Dict):
        """ Add situations into graph: for each event that was linked to a frame """
        for event, info in events_info.items():
            if info.get("most_similar_frame"):
                frame = info['most_similar_frame']['name']
                graph.add((URIRef(event), self.rdf.type, self.dul.Situation))
                graph.add((URIRef(event), self.dul.satisfies, URIRef(frame)))

                if isinstance(info['srl'], pd.DataFrame):
                    for _, row in info['srl'].iterrows():
                        graph = self.add_roles_in_graph(row=row, graph=graph,
                                                        frame=frame, event=event)

        return graph

    def init_graph(self):
        """ Init KG: bind namespaces """
        graph = Graph()
        graph.bind("dul", self.dul)
        graph.bind("rdf", self.rdf)
        graph.bind("premon", self.premon)
        return graph

    def get_iri_frame_element(self, label: str, frame_name: str):
        """ Reverse engineer: from frame element label to uri """
        frame_name = frame_name.split("/")[-1].lower()

        # Framester
        # return f"{self.fe_prefix}/{label.replace(' ', '_')}.{frame_name}"

        # PreMon
        # http://premon.fbk.eu/resource/fn17-change_of_leadership@side_1
        label = label.replace(" ", "_").lower()
        return f"{self.premon}fn17-{frame_name}@{label}"

    def __call__(self, events_info: Dict):
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
    # ap.add_argument('-m', "--mapping", required=True,
    #                 help="`mapping_fe_subclass_path` in GraphBuilder class")
    ap.add_argument('-o', "--output", required=True,
                    help="output path to save data")
    args_main = vars(ap.parse_args())

    with open(args_main["events_info"], "rb") as openfile:
        EVENTS_INFO = pickle.load(openfile)

    # GRAPH_BUILDER = GraphBuilder(mapping_fe_subclass_path=args_main["mapping"])
    GRAPH_BUILDER = GraphBuilder()
    LOGGER = Logger()

    LOGGER.log_start(name="Building graph")
    RES = GRAPH_BUILDER(events_info=EVENTS_INFO)
    LOGGER.log_end()

    RES.serialize(destination=args_main["output"], format="turtle")
