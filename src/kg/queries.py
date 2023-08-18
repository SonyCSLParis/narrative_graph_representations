"""
Queries to retrieve information from manual examples
Cf notebook: manual-example/query_graph.ipynb """
# -*- coding: utf-8 -*-


#### SIMPLE RDF

PREFIXES = """
PREFIX wd: <http://www.wikidata.org/entity/> 
PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> 
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
PREFIX ex: <http://example.com/> 
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
PREFIX ti: <http://www.ontologydesignpatterns.org/cp/owl/timeinterval.owl#> 
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
PREFIX wn30instances: <https://w3id.org/framester/wn/wn30/instances/> 
PREFIX own2dul: <http://www.ontologydesignpatterns.org/ont/own3/own2dul.owl#> 
PREFIX framesterschema: <https://w3id.org/framester/schema/> 
PREFIX framstersyn: <https://w3id.org/framester/data/framestersyn/> 
PREFIX framestercore: <https://w3id.org/framester/data/framestercore/> 
PREFIX framesterrole: <https://w3id.org/framester/data/framesterrole/agent> 
PREFIX framester-aboxfe: <https://w3id.org/framester/framenet/abox/fe/> 
PREFIX faro: <http://purl.org/faro/> 
PREFIX sioc: <http://rdfs.org/sioc/ns#> 
PREFIX prov: <http://www.w3.org/ns/prov#> 
PREFIX wikipedia-en: <http://en.wikipedia.org/wiki/> 
PREFIX nif: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#> 
PREFIX schema: <http://schema.org/> 
PREFIX F: <http://isweb.uni-koblenz.de/eventmodel/> 
PREFIX dbr: <http://dbpedia.org/resource/> 
"""

## AGENTS (INCL. TYPE+PARTICIPANT)
QUERY_EVENT_PARTICIPANT = PREFIXES + """
SELECT ?e ?class ?participant ?type_p WHERE {
    ?class rdfs:subClassOf* dul:Event .
    ?prop rdfs:subPropertyOf* dul:hasParticipant .
    ?e rdf:type ?class ;
       dul:hasParticipant ?participant .
    ?participant a ?type_p .

}   
"""

QUERY_PARTICIPANT_ATTRIBUTES = PREFIXES + """
SELECT ?participant ?p ?o WHERE {
    ?class rdfs:subClassOf* dul:Event .
    ?prop rdfs:subPropertyOf* dul:hasParticipant .
    ?e rdf:type ?class ;
       dul:hasParticipant ?participant .
    ?participant ?p ?o .

}   
"""

## ROLES (INCL. PARTICIPANT)
QUERY_ROLES = PREFIXES + """
SELECT DISTINCT ?d ?s ?concept ?object WHERE {
    ?prop_d rdfs:subPropertyOf* dul:defines .
    ?prop_i rdfs:subPropertyOf* dul:includesObject .
    ?d rdf:type dul:Description ;
       ?prop_d ?concept .
    ?concept rdf:type dul:Role ;
             dul:classifies ?object .
    ?s rdf:type dul:Situation ;
       dul:satisfies ?d ;
       ?prop_i ?object .
}
"""

## EVENTS/ACTIONS (RELATION BETWEEN EVENTS, TYPES)
QUERY_REL_EVENTS = PREFIXES + """
SELECT ?e1 ?class1 ?e2 ?class2 ?p1 ?p2 WHERE {
    ?class1 rdfs:subClassOf* dul:Event .
    ?e1 rdf:type ?class1 .
    ?class2 rdfs:subClassOf* dul:Event .
    ?e2 rdf:type ?class2 .
    {?e1 ?p1 ?e2} UNION { ?e2 ?p2 ?e1} .
}
"""

QUERY_EVENT_TYPES = PREFIXES + """
SELECT DISTINCT ?object ?concept WHERE {
    ?concept rdf:type dul:EventType ;
             dul:classifies ?object .
}
"""

## PROVENANCE
QUERY_PROV = PREFIXES + """
SELECT DISTINCT ?s ?o ?p1 ?o1 WHERE {
   ?s prov:wasInformedBy ?o ;
      ?p1 ?o1 .
}
"""

## LOCATION
QUERY_LOC = PREFIXES + """
SELECT DISTINCT ?s ?o WHERE {
   ?s dul:hasLocation ?o .
}
"""

## TIME
QUERY_PIT = PREFIXES + """
SELECT ?event ?pit WHERE {
   ?event dul:isObservableAt ?pit .
}
"""

QUERY_TI = PREFIXES + """
SELECT ?s ?ti ?pit ?start ?end WHERE {
   ?s dul:Time ?ti .
   OPTIONAL {?ti ti:hasIntervalDate ?pit .}
   OPTIONAL {?ti ti:hasIntervalStartDate ?start .}
   OPTIONAL {?ti ti:hasIntervalEndDate ?end .}
}
"""

## (PHYSICAL) OBJECTS
QUERY_OBJECT = PREFIXES + """
SELECT ?s ?class ?e WHERE {
   ?class rdfs:subClassOf* dul:PhysicalObject .
   ?s rdf:type ?class ;
      dul:isParticipantIn ?e.
}
"""

## TEMPLATE DESCRIPTIONS
QUERY_TEMPLATE_DS = PREFIXES + """
SELECT ?des ?sit ?o ?node ?prop WHERE {
   ?prop rdfs:subPropertyOf* dul:defines .
   ?sit dul:satisfies ?des ;
        ?p ?o .
   ?des ?prop ?node .
   ?node dul:classifies ?o .
   VALUES (?des) {
      ( <to-replace> )
      }
}
"""

## STATE
QUERY_STATE = QUERY_TEMPLATE_DS.replace(
   "<to-replace>", "ex:StateChangeDescription")

## GOAL, TASK
QUERY_GOAL = QUERY_TEMPLATE_DS.replace(
   "<to-replace>", "ex:Coup_to_take_power_alone")

## OUTCOME-EFFECT: cf. relations between events, state

## PERSPECTIVE
QUERY_PERSPECTIVE = QUERY_TEMPLATE_DS.replace(
   "<to-replace>", "ex:EventSentimentInterpretationDescription")


## SCRIPT (all the above - using the description template - can be considered script)
# Querying all such descriptions with the query below
QUERY_SCRIPT = QUERY_TEMPLATE_DS.replace(
   "VALUES (?des) {\n      ( <to-replace> )\n      }", "")

## STORYLINE (all the above situations - queries through the description template -
## can be seen as storylines)
