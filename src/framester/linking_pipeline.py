"""
Linking KGs: generic and linguistic
"""
# -*- coding: utf-8 -*-
from rdflib.namespace import OWL
from src.kg.hdt_kg import HDTKG
from src.kg.sparql_kg import SPARQLInterface

class LinkingKGPipeline:
    """ All steps to link multiple KGs """

    def __init__(self, generic_kg: HDTKG, linguistic_kg: SPARQLInterface):
        self.generic_kg = generic_kg
        self.linguistic_kg = linguistic_kg

        self.discarded_types = [
            str(OWL.Thing)
        ]

    def __call__(self, node):
        """ Main """
        type_node = self.generic_kg.get_type_node(node)
        type_node.extend(self.linguistic_kg.get_type_node(node))
        type_node = list(set(x for x in type_node if x not in self.discarded_types))

        # Adding equivalent classes 
        type_node = [(x, self.generic_kg.get_equivalent_class_yago(node=x)) for x in type_node]
        frames = self.linguistic_kg.get_frames(nodes_info=type_node)
        frame_elements = [self.linguistic_kg.get_frame_elements(frame=frame) for frame in frames]

        return type_node, frames, frame_elements
