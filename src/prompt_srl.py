"""
5th step of the pipeline: prompt for srl
"""
# -*- coding: utf-8 -*-
import argparse
import pickle
from io import StringIO
from typing import List
from types import NoneType
from tqdm import tqdm
import pandas as pd
import openai
from settings import OPENAI_KEY
from src.logger import Logger

openai.api_key = OPENAI_KEY

class PromptSRL:
    """ Using LLM to extract semantic roles """
    def __init__(self):
        self.template = self.init_prompt_template()

    @staticmethod
    def get_completion(prompt: str, model: str ="gpt-3.5-turbo"):
        """ Call API with prompt"""
        messages = [{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0, # this is the degree of randomness of the model's output
        )
        return response.choices[0].message["content"]

    @staticmethod
    def init_prompt_template():
        """ Prompt template """
        return """
        I will give you (1) a text event description (2) an associated frame (from frame semantics) and its roles.
        You need to fill (i) the roles based on (1) and (ii) the corresponding DBpedia IRI. 
        If the answer is not in the text, both (i) and (ii) should be <unknown>.

        The output should be in a csv format with the following columns: 'role name', 'role text' and 'role iri'.

        ```text
        {event_description}
        ```

        ```frame
        {frame}
        ```

        ```roles
        {roles}
        ```
        """

    @staticmethod
    def pre_process_frame_name(name: str) -> str:
        """ From IRI to readable frame name """
        return name.split('/')[-1].replace("_", " ").lower()

    @staticmethod
    def format_frame_elements(frame_elements: List[str]) -> str:
        """ Format for prompt """
        frame_elements = [x.split("/")[-1].split(".")[0] \
            .replace("_", " ") for x in frame_elements]
        return "- " + "\n- ".join(frame_elements)

    def fill_template(self, event_info: dict) -> str:
        """ Replace template with slots
        event_info: values from dict obtained in `combine_event_frame_data.py` """
        if event_info.get("frames_with_des") and not isinstance(event_info.get('description_embedding'), NoneType):
            frame = self.pre_process_frame_name(event_info['most_similar_frame']['name'])
            roles = self.format_frame_elements(event_info['most_similar_frame']['frame_elements'])
            template = self.template \
                .replace("{event_description}", event_info['description'][0]) \
                    .replace("{frame}", frame) \
                        .replace("{roles}", roles)
            return template
        return None

    def __call__(self, events_info: dict) -> dict:
        """ Main """
        events = list(events_info.keys())
        for i in tqdm(range(len(events))):
            event = events[i]
            event_info = events_info[event]

            prompt = self.fill_template(event_info=event_info)
            output = self.get_completion(prompt=prompt)

            if not isinstance(output, NoneType):
                df_res = pd.read_csv(StringIO(output), sep=',')
                events_info[event]["srl"] = df_res
            else:
                events_info[event]["srl"] = None
        
        return events_info


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-e', "--events_info", required=True,
                    help="events_info, cf `combine_event_frame_data.py`")
    ap.add_argument('-o', "--output", required=True,
                    help="output path to save data")
    args_main = vars(ap.parse_args())

    with open(args_main["events_info"], "rb") as openfile:
        EVENTS_INFO = pickle.load(openfile)
    
    PROMPT_SRL = PromptSRL()
    LOGGER = Logger()

    LOGGER.log_start(name="Prompt SRL + GPT")
    RES = PROMPT_SRL(events_info=EVENTS_INFO)
    LOGGER.log_end()

    with open(args_main["output"], "wb") as openfile:
        pickle.dump(RES, openfile)