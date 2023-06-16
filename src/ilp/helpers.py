""" Helpers to extract information for the ILP problem """
# -*- coding: utf-8 -*-
import pandas as pd

def check_if_concepts(row, concepts) -> bool:
    """ Check if row corresponds to concept """
    if isinstance(row.concepts, str) and \
        row.concepts.replace("<concept>", "").strip() in concepts.values():
        return True
    return False

def update_models(models: dict, models_keep: dict) -> dict:
    """ Filtering models """
    models = {i: name for i, name in models.items() if models_keep[name]}
    models = {i: models[val] for i, val in enumerate(sorted(models.keys()))}
    return models

def extract_concept_model(df_info: pd.DataFrame,
                          concepts: dict, models: dict) -> pd.DataFrame:
    """ From .csv of gsheet extract matrix # concepts * # models """
    # filtering on concepts --> filtering on column `concepts`
    filtered_df = df_info[
        df_info.apply(lambda row: check_if_concepts(row, concepts=concepts), axis=1)]

    # filtering on models --> filtering on columns
    filtered_df = filtered_df[list(models.values())]

    return filtered_df
