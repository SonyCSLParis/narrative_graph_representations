"""
SPARQL
"""
# -*- coding: utf-8 -*-
import io
from typing import List, Tuple
import requests
import numpy as np
import pandas as pd
from rdflib.namespace import OWL, RDFS, RDF, SKOS

class SPARQLInterface:
    """ Main class to interact with SPARQL endpoint """
    def __init__(self, sparql_endpoint: str):

        self.sparql_endpoint = sparql_endpoint

        self.prefixes = {
            "owl": str(OWL),
            "framester-schema": "https://w3id.org/framester/schema/",
            "rdfs": str(RDFS),
            "framenet-tbox": "https://w3id.org/framester/framenet/tbox/",
            "rdf": str(RDF),
            "dbpedia-yago": "http://dbpedia.org/class/yago/",
            "skos": str(SKOS)
        }
        self.prefix_query = "\n".join([f"PREFIX {key}: <{val}>" \
            for key, val in self.prefixes.items()])
        self.init_templates_query()

    def init_templates_query(self):
        """ 
        Templates for SPARQL queries
        VALUES ?z { "abc" "def" } """
        self.templates = {
            "tq_frames_from_yago_wordnet": self.prefix_query + \
            """
            SELECT DISTINCT ?frame_framester ?frame_framenet
            WHERE {
                ?s owl:sameAs ?wn30instances_synset .
                ?framestersyn_noun framester-schema:unaryProjection ?wn30instances_synset;
                                rdfs:subClassOf ?frame_framester .
                ?frame_framester owl:sameAs ?frame_framenet .
                VALUES ?s { <to-change> }
            }   
            """,
            "tq_frames_from_dbpedia_yago": self.prefix_query + \
            """
            SELECT DISTINCT ?frame_framester ?frame_framenet
            WHERE {
                ?s skos:exactMatch ?wn30instances_synset .
                ?framestersyn_noun framester-schema:unaryProjection ?wn30instances_synset;
                                rdfs:subClassOf ?frame_framester .
                ?frame_framester owl:sameAs ?frame_framenet .
                VALUES ?s { <to-change> }
            }   
            """,
            "tq_frame_elements": self.prefix_query + \
            """
            SELECT DISTINCT ?frame_element ?type_fe ?comment WHERE {
            <frame-to-change> framenet-tbox:hasFrameElement ?frame_element .
            ?frame_element framenet-tbox:FE_coreType ?type_fe ;
                        rdfs:comment ?comment .
            # OPTIONAL {?frame_element rdfs:range ?range } .
            # OPTIONAL {?range rdfs:subClassOf ?super_range } .
            } 
            """,
            "tq_type_node": self.prefix_query + \
            """
            SELECT DISTINCT * WHERE {   
                <node-to-change> rdf:type ?o .   
            }
            """,
            "tq_comment_node": self.prefix_query + \
            """
            SELECT DISTINCT * WHERE {   
                <node-to-change> rdfs:comment ?o .   
            }
            """
        }

    def get_type_node(self, node: str) -> np.ndarray:
        """ Retrieve rdf:type of input nodes """
        query = self.templates["tq_type_node"].replace("node-to-change", node)
        res = self.run_query(query)
        return res.o.unique()

    def get_comment_node(self, node: str) -> np.ndarray:
        """ Retrieve rdfs:comment of input nodes """
        query = self.templates["tq_comment_node"].replace("node-to-change", node)
        res = self.run_query(query)
        return res.o.unique()

    def get_frames(self, nodes_info: Tuple[str, List[str]],
                   to_discard: List[str]) -> List[str]:
        """ Retrieve frames 
        Removing frames from to_discard list """
        yago_wordnet = [x for node_info in nodes_info for x in node_info[1]]
        query = self.templates["tq_frames_from_yago_wordnet"].replace(
                "<to-change>", " ".join([f"<{x}>" for x in yago_wordnet]))
        df_ = self.run_query(query=query)
        df_.columns = ["frame_framester", "frame_framenet"]
        res = list(df_.frame_framenet.values)

        dbpedia_yago = [node_info[0] for node_info in nodes_info if not node_info[1]]
        query = self.templates["tq_frames_from_dbpedia_yago"].replace(
            "<to-change>", " ".join([f"<{x}>" for x in dbpedia_yago]))
        df_ = self.run_query(query=query)
        df_.columns = ["frame_framester", "frame_framenet"]
        res.extend(list(df_.frame_framenet.values))

        res = [x for x in res if x not in to_discard]
        return list(set(x for x in res if isinstance(x, str)))

    def get_frame_elements(self, frame: str) -> List[str]:
        """ Retrieve frame elements """
        query = self.templates["tq_frame_elements"].replace(
            "frame-to-change", frame)
        output = self.run_query(query=query)
        return list(output.frame_element.values), \
            list(output.type_fe.values), \
                list(output.comment.values)

    def run_query(self, query) -> pd.DataFrame:
        """ Using curl requests to run query """
        response = requests.get(
            self.sparql_endpoint, headers={"Accept": "text/csv"},
            params={"query": query}, timeout=3600)
        # print(response.url)
        return pd.read_csv(io.StringIO(response.content.decode('utf-8')))


if __name__ == '__main__':
    from settings import FRAMESTER_ENDPOINT
    NODE = "http://dbpedia.org/resource/French_Revolution"
    interface = SPARQLInterface(sparql_endpoint=FRAMESTER_ENDPOINT)
    print(interface.get_type_node(node=NODE))
