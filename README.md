# Structured Representations for Narratives

This is the code for the paper submitted to K-CAP 2023: "Structured Representations for Narratives".

First clone the repo
```bash
git clone https://github.com/SonyCSLParis/narrative_graph_representations
```
---
## 1. Set Up Virtual Environment

Python version used: 3.10.6. We recommend to use a virtual environment.

Install the requirements:
```bash
pip install -r requirements.txt
````

Install the spacy model:
```python
python -m spacy download en_core_web_sm
```

Errors when installing:
- For `hdt`, make sure to have `pybind11`` installed. Also make sure that you have installed the pre-requisites before: [here](https://github.com/Callidon/pyHDT).
- For `bertopic`+`conda`, you might need to install llvmlite
    ```bash
    conda install -c numba llvmlite
    ```
- If you work on an Apple Silicon Machine + conda, you might later be prompted to download again `grpcio`, you can do it using:
    ```bash
    conda install grpcio=1.43.0 -c conda-forge
    ```

Create a `private.py` file in the settings folder and add the followings:
* `FOLDER_PATH`: (of git repository on your machine)
* `FRAMESTER_ENDPOINT`: Framester endpoint (either the public one, or a local endpoint)
* `OPENAI_KEY`: OpenAI API key
* `FOLDER_HDT_GEN_DB`: HDT path to main DBpedia
* `FOLDER_HDT_GEN_DB_TYPES`: same as above, but for dbpedia extensive types

Then run the following for setting up the packages
```bash
python setup.py install
```
---

## 2. Data Download/Setup

* [Triply DB](https://triply.cc)'s HDT version of DBpedia (snapshot 2021-09)
* [Additional DBpedia types](https://databus.dbpedia.org/dbpedia/collections/dbpedia-snapshot-2022-03): dbpedia-instance-types_lang=en_specific.ttl, dbpedia-instance-types_lang=en_transitive.ttl, dbpedia-instance-types_tag=specific.ttl, dbpedia-sdtypes_lang=en.ttl 
* [Framester](https://framester.github.io): We strongly recommend to set up a local API for Framester. We used GraphDB, and loaded it without reasoning.

These can also be sent upon request.

---
## 3. Pipeline

The `src/pipeline/main.py` file runs all the components in the pipeline.

1. **Retrieve info about events**: `src/pipeline/retrieve_event_info.py`
2. **Map DBpedia to Framester**: `src/pipeline/map_type_to_frame.py`
3. **Retrieve info about frames**: `src/pipeline/retrieve_frame_info.py`
4. **Combine info in a single file**: `src/pipeline/combine_event_frame_data.py`
5. **Prompting using OpenAI LLM**: `src/pipeline/prompt_srl.py`
6. **Run DBpedia Spotlight**: `src/pipeline/enrich_srl.py`
7. **Build the graph**: `src/pipeline/build_graph.py`

To run the pipeline, you need to have a `.csv` file with your DBpedia events, in an entity `column`.

```python
python src/pipeline/main.py -m <embedding-model> -i <input-event-csv-file> -o <output-folder>

