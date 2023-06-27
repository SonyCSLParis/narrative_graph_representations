

ILP with Pulp to find which models to use to satisfy set of narrative concept requirement

F&A:
* identified common concepts across several models + 6 projects across MUHAI
* mapped these concepts to the models (does model X encode concept Y?)

I added other event ontologies and mapped them to the narrative concept

Users chooses in .yaml
* the narrative concepts they need for their representation (limitation: can only choose among the ones defined by us)
* the models they want to keep (if for some reason they want to discard models, that's possible)

First use: possible to generate the setting in a .yaml file, cf `src/ilp/generate_yaml_settings.py` --> by default everything will be set to 1, the user has to change the values 

ILP program finds set of models to use, following these constraints:
* each narrative concept should be encoded in at least of the selected models
* the number of models used should be minimised (therefore will prefer model X that covers set of concepts A and B rather than model X1 that covers A and models X2 that covers B)

Repository organisation
* `data/`: concrete outputs
* `resources/`: downloaded ontologies when looking for narrative concepts
* `src/`: core code 


hdt+pybind11
conda install -c numba llvmlite (for bertopic)

conda install grpcio=1.43.0 -c conda-forge