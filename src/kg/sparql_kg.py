"""
SPARQL
"""
# -*- coding: utf-8 -*-
import io
import requests
import pandas as pd
from typing import List, Dict, Tuple
from rdflib.namespace import OWL, RDFS, RDF, SKOS

class SPARQLInterface:
    """ Main class to interact with SPARQL endpoint """
    def __init__(self, sparql_endpoint: str):

        self.sparql_endpoint = sparql_endpoint
        self.headers = {"Accept": "text/csv"}

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
        """ VALUES ?z { "abc" "def" } """
        self.tq_frames_from_yago_wordnet = self.prefix_query + \
        """
        SELECT DISTINCT ?frame_framester ?frame_framenet
        WHERE {
            ?s owl:sameAs ?wn30instances_synset .
            ?framestersyn_noun framester-schema:unaryProjection ?wn30instances_synset;
                               rdfs:subClassOf ?frame_framester .
            ?frame_framester owl:sameAs ?frame_framenet .
            VALUES ?s { <to-change> }
        }   
        """

        self.tq_frames_from_dbpedia_yago = self.prefix_query + \
        """
        SELECT DISTINCT ?frame_framester ?frame_framenet
        WHERE {
            ?s skos:exactMatch ?wn30instances_synset .
            ?framestersyn_noun framester-schema:unaryProjection ?wn30instances_synset;
                               rdfs:subClassOf ?frame_framester .
            ?frame_framester owl:sameAs ?frame_framenet .
            VALUES ?s { <to-change> }
        }   
        """

        self.tq_frame_elements = self.prefix_query + \
        """
        SELECT DISTINCT ?frame_element WHERE {
        <frame-to-change> framenet-tbox:hasFrameElement ?frame_element .
        OPTIONAL {?frame_element rdfs:range ?range } .
        OPTIONAL {?range rdfs:subClassOf ?super_range } .
        } 
        """

        self.tq_type_node = self.prefix_query + \
        """
        SELECT DISTINCT * WHERE {   
            <node-to-change> rdf:type ?o .   
        }
        """

    def get_type_node(self, node: str):
        """ Retrieve rdf:type of input nodes """
        query = self.tq_type_node.replace("node-to-change", node)
        res = self.run_query(query)
        return (res.o.unique())

    def get_frames(self, nodes_info: Tuple[str, List[str]]):
        """ Retrieve frames """
        yago_wordnet = [x for node_info in nodes_info for x in node_info[1]]
        query = self.tq_frames_from_yago_wordnet.replace(
                "<to-change>", " ".join([f"<{x}>" for x in yago_wordnet]))
        df = self.run_query(query=query)
        df.columns = ["frame_framester", "frame_framenet"]
        res = list(df.frame_framenet.values)

        dbpedia_yago = [node_info[0] for node_info in nodes_info if not node_info[1]]
        query = self.tq_frames_from_dbpedia_yago.replace(
            "<to-change>", " ".join([f"<{x}>" for x in dbpedia_yago]))
        df = self.run_query(query=query)
        df.columns = ["frame_framester", "frame_framenet"]
        res.extend(list(df.frame_framenet.values))

        return list(set(x for x in res if isinstance(x, str)))
    
    def get_frame_elements(self, frame: str) -> List[str]:
        """ Retrieve frame elements """
        query = self.tq_frame_elements.replace(
            "frame-to-change", frame)
        return list(self.run_query(query=query).frame_element.unique())


    def run_query(self, query):
        """ Using curl requests to run query """
        response = requests.get(
            self.sparql_endpoint, headers=self.headers,
            params={"query": query}, timeout=3600)
        # print(response.url)
        return pd.read_csv(io.StringIO(response.content.decode('utf-8')))

"""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#> 
PREFIX framester-schema: <https://w3id.org/framester/schema/> 
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX framenet-tbox: <https://w3id.org/framester/framenet/tbox/>
PREFIX yago-res: <http://yago-knowledge.org/resource/>
PREFIX wn30instances: <https://w3id.org/framester/wn/wn30/instances/> 
PREFIX frame-abox-frame: <https://w3id.org/framester/framenet/abox/frame/>
PREFIX frame-abox-semtype: <https://w3id.org/framester/framenet/abox/semType/>
PREFIX framestesyn: <https://w3id.org/framester/data/framestersyn/>
PREFIX framestercore: <https://w3id.org/framester/data/framestercore/>
PREFIX framenet-abox-fe: <https://w3id.org/framester/framenet/abox/fe/>
PREFIX do: <http://www.ontologydesignpatterns.org/ont/d0.owl#>
PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#>
PREFIX semiotics: <http://www.ontologydesignpatterns.org/cp/owl/semiotics.owl#>

SELECT DISTINCT * WHERE {
  yago-res:wordnet_revolution_107424109 owl:sameAs ?wn30instances_synset .
  ?framestersyn_noun framester-schema:unaryProjection ?wn30instances_synset;
                     rdfs:subClassOf ?frame_framester .
  ?frame_framester owl:sameAs ?frame_framenet .
  ?frame_framenet framenet-tbox:hasFrameElement ?frame_element .
  ?frame_element rdfs:range ?range .
  ?range rdfs:subClassOf ?super_range .
} 
"""

if __name__ == '__main__':
    from settings import FRAMESTER_ENDPOINT
    NODE = "http://dbpedia.org/resource/French_Revolution"
    interface = SPARQLInterface(sparql_endpoint=FRAMESTER_ENDPOINT)
    print(interface.get_type_node(node=NODE))