""" Context knowledge for solving ILP problem
- Concepts: the ones needed for a narrative
- Models: existing ontologies
- Requirements: choosing concepts"""
# -*- coding: utf-8 -*-

CONCEPTS  = {
    0: 'agent',
    1: '<agent> type + hierarchy + property',
    2: 'role',
    3: '<role> participant',
    4: 'event',
    5: '<event> relations between events',
    6: '<event> type + hierarchy',
    7: 'provenance',
    8: 'location',
    9: '<location> relations between locations',
    10: 'action',
    11: '<action> type',
    12: '<action> relation between actions',
    13: '<action> conditions',
    14: 'time-calculus',
    15: 'object+type',
    16: 'state',
    17:'goal',
    18: 'outcome-effect',
    19: 'perspective',
    20: 'script',
    21: 'storyline',
    22: 'context'
}

MODELS = {
    0: 'm1-rst',
    1: 'm2-meghini-cidoc-crm',
    2: 'm3-mediation',
    3: 'm4-mythology',
    4: 'm5-bletchey-cidoc',
    5: 'm6-gtn-causal',
    6: 'm7-bkonto-biography',
    7: 'm8-ody-ont-proton',
    8: 'm9-propp-fairy-tale',
    9: 'm10-transmedia-fiction',
    10: 'm11-lit-drammar-dolce',
    11: 'cidoc-crm',
    12: 'dul (dolce+dns)',
    13: 'event-calculus',
    14: 'eo',
    15: 'f',
    16: 'sem',
    17: 'abc',
    18: 'lode',
    19: 'e'
}
