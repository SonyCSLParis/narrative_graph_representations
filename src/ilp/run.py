""" LP solver to choose the ontology models for narrative representations 
A bit more complicated than Ax = b
A concept model
b requirements 


Documentation: https://coin-or.github.io/pulp/index.html

"""
# -*- coding: utf-8 -*-
import argparse
import yaml
import numpy as np
import pandas as pd
from pulp import LpVariable, LpProblem, LpMinimize, LpInteger, LpStatus

from src.ilp.helpers import update_models, extract_concept_model
from src.ilp.setting import CONCEPTS, MODELS

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-s', "--settings", required=True,
                    help=".yaml file with settings for ILP")
    ap.add_argument('-t', "--table", required=True,
                    help=".csv file downloaded directly from gsheet")
    args_main = vars(ap.parse_args())

    with open(args_main["settings"], 'rb') as openfile:
        SETTINGS = yaml.load(openfile, Loader=yaml.FullLoader)

    CONCEPTS_REQ = SETTINGS['concepts_req']
    MODELS_KEEP = SETTINGS['models_keep']

    U_MODELS = update_models(models=MODELS, models_keep=MODELS_KEEP)

    DF = pd.read_csv(args_main["table"]).fillna(0)
    CONCEPT_MODEL = extract_concept_model(df_info=DF, concepts=CONCEPTS, models=U_MODELS) \
        .to_numpy()

    REQUIREMENTS = np.array([CONCEPTS_REQ[concept] \
        for _, concept in sorted(CONCEPTS.items(), key=lambda x: x[0])])

    VARIABLES = np.array([LpVariable(U_MODELS[i], 0, 1, LpInteger) \
        for i in U_MODELS])

    ILP_PROB = LpProblem("findModels", LpMinimize)

    # Add constraints
    for i, constraint in enumerate(np.matmul(CONCEPT_MODEL, VARIABLES)):
        ILP_PROB += constraint >= REQUIREMENTS[i]
    # Add objective
    ILP_PROB += VARIABLES.sum()

    ILP_PROB.writeLP("findModel.lp")
    ILP_PROB.solve()

    print(f"================\nStatus: {LpStatus[ILP_PROB.status]}\n")

    print("Your narrative concepts requirements:\n")
    for name, val in CONCEPTS_REQ.items():
        print(f"{val}:\t{name}")
    
    print("\nModel selection:")
    for v in ILP_PROB.variables():
        if v.name != "__dummy":
            print(f"{int(v.varValue)}:\t{v.name}")
