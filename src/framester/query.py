"""
Main helper functions to query Framester HDT
"""
# -*- coding: utf-8 -*-

from rdflib.namespace import RDF
from rdflib import Namespace

TBOX = Namespace("https://w3id.org/framester/framenet/tbox/")

def get_triples(doc, sub, obj, pred):
    """ From HDT document doc, get triples in a list"""
    return list(doc.search_triples(sub, obj, pred)[0])

def get_frames(hdt_doc):
    """ Extract all frames """
    triples = get_triples(hdt_doc, "", str(RDF.type), str(TBOX.Frame))
    return (list(set(x[0] for x in triples)))

def get_frame_element(hdt_doc, frame):
    """ Extract frame elements of a given frame """
    return get_triples(hdt_doc, "", str(TBOX.frameElementOf), frame)
