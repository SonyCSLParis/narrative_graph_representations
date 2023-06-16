""" From variables in ./setting.py, generate yaml setting file """

import yaml
import argparse
from collections import OrderedDict
from src.ilp.setting import CONCEPTS, MODELS

def main_generate_setting(save_path: str):
    """ Save yaml file with parameters: default all True """
    settings = {
        "concepts_req": {CONCEPTS[i]: 1 for i in sorted(CONCEPTS.keys())},
        "models_keep": {MODELS[i]: 1 for i in sorted(MODELS.keys())}
    }
    with open(save_path, 'w') as outfile:
        yaml.dump(settings, outfile)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-s', "--save_path", required=True,
                    help=".yaml file name to save settings")
    args_main = vars(ap.parse_args())

    main_generate_setting(save_path=args_main['save_path'])
