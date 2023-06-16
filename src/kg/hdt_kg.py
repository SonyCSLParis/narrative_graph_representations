"""
HDT class
"""
# -*- coding: utf-8 -*-
import os
import fnmatch
from typing import List, Dict, Tuple
from hdt import HDTDocument
from rdflib import OWL


class HDTKG:
    """ Main class to query KG in HDT format """
    def __init__(self, folder_hdt: str, nested_dataset: bool, config: Dict):
        self.docs = self.load_hdt_documents(folder_hdt, nested_dataset)
        self.config = config

        self.owl_equivalent_class = str(OWL.equivalentClass)

    def load_one_folder(self, folder_hdt: str) -> List[HDTDocument]:
        """ Retrieve HDT doc from one folder """
        dirs = [os.path.join(folder_hdt, folder) for folder in os.listdir(folder_hdt) \
            if not folder.startswith(".")]
        dirs = [os.path.join(old_dir, new_dir, "hdt") \
            for old_dir in dirs for new_dir in os.listdir(old_dir)]
        dirs = [elt for elt in dirs if not elt.split('/')[-2].startswith(".")]
        dirs = [elt for elt in dirs if os.path.exists(elt)]
        return [HDTDocument(file) for file in dirs]

    def load_hdt_documents(self, folders_hdt: List[str], nested_dataset: bool) -> List[HDTDocument]:
        """ Retrieve all hdt documents (if nested: several, else 1) """
        docs = []
        for folder in folders_hdt:
            if nested_dataset:
                docs.extend(self.load_one_folder(folder_hdt=folder))

            else:
                docs.extend([HDTDocument(os.path.join(folder, file)) for file in os.listdir(folder) \
                    if fnmatch.fnmatch(file, "*.hdt")])
        return docs

    def get_triples(self, **params: Dict) -> List[Tuple[str, str, str]]:
        """ Querying HDT dataset and retrieve triples """
        subject_t = params.get('subject', '')
        predicate_t = params.get('predicate', '')
        object_t = params.get('object', '')

        triples = []
        for doc in self.docs:
            curr_triples, _ = doc.search_triples(subject_t, predicate_t, object_t)
            triples.extend(curr_triples)

        return list(set(triples))

    def get_type_node(self, node: str) -> List[str]:
        """ Retrieve type of nodes """
        params = {"subject": node, "predicate": self.config["rdf_type"]}
        return [x[2] for x in self.get_triples(**params)]

    def get_equivalent_class_yago(self, node: str) -> List[str]:
        """ Map DBpedia YAGO IRI to YAGO Wordnet IRI (example below)
        <http://dbpedia.org/class/yago/Ability105616246> <http://www.w3.org/2002/07/owl#equivalentClass> <http://yago-knowledge.org/resource/wordnet_ability_105616246> .
        """
        params = {"subject": node, "predicate": self.owl_equivalent_class}
        return [x[2] for x in self.get_triples(**params)]
