"""
5th step of the pipeline: prompt for srl
"""
# -*- coding: utf-8 -*-
import argparse
import pickle
from io import StringIO
from typing import List
from types import NoneType
from collections import defaultdict
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
        self.fe_prefix = "https://w3id.org/framester/framenet/abox/fe"

    @staticmethod
    def get_completion(prompt: str, model: str ="gpt-3.5-turbo") -> str:
        """ Call API with prompt"""
        messages = [{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0, # this is the degree of randomness of the model's output
        )
        return response.choices[0].message["content"]

    @staticmethod
    def init_prompt_template() -> str:
        """ Prompt template """
        prompt = """
        ```Prompt:
        Extract Semantic Roles (from frame semantics) from the following  text. Focus on the main points and important details.
        ```

        ```Semantic Roles:
        Each role is given with its description: - <role name>: <role description>
        {semantic_roles}
        ```

        ```Frame:
        {frame}
        ```

        ```Text:
        {event_description}
        ```

        ```Instructions:
        1. Identify the Semantic Roles in the `Text`. Focus on the most important.
        2. If possible, find the corresponding DBpedia IRI.
        2. If the answer is not in the text, output `<unknown>`.
        3. Output the answers in a csv format with the columns: `role_name`, `role_iri` and `role_text`.
        ```
        """
        return prompt

    @staticmethod
    def pre_process_frame_name(name: str) -> str:
        """ From IRI to readable frame name """
        return name.split('/')[-1].replace("_", " ").lower()

    @staticmethod
    def format_semantic_roles(frame_elements: List[str], comments: List[str]) -> str:
        """ Format for prompt """
        frame_elements = [x.split("/")[-1].split(".")[0] \
            .replace("_", " ") for x in frame_elements]
        return "\n- " + "\n- ".join([f"{f_elt}: {comments[i]}" \
            for i, f_elt in enumerate(frame_elements)])

    def fill_template(self, event_info: dict) -> str:
        """ Replace template with slots
        event_info: values from dict obtained in `combine_event_frame_data.py` """
        if event_info.get("frames_with_des") and \
            not isinstance(event_info.get('description_embedding'), NoneType):
            frame = self.pre_process_frame_name(event_info['most_similar_frame']['name'])
            roles = event_info['most_similar_frame']['frame_elements']
            comments = event_info['most_similar_frame']['comments']

            template = self.template.replace(
                "{event_description}", event_info['description'][0])
            template = template.replace(
                "{frame}", frame)
            template = template.replace(
                "{semantic_roles}", self.format_semantic_roles(roles, comments))
            return template
        return None

    def update_info(self, event_info: dict) -> dict:
        """ Updating df for easier pre-processing
        - adding iri column
        - adding type of fe (core/peripheral/etc) """
        df_srl = event_info["srl"]
        frame_name = event_info["most_similar_frame"]["name"].split("/")[-1].lower()
        df_srl["role_name_iri"] = df_srl["role_name"].apply(
            lambda x: f"{self.fe_prefix}/{x.replace(' ', '_')}.{frame_name}")

        most_similar_frame = event_info["most_similar_frame"]
        frame_element_to_type = {
            most_similar_frame["frame_elements"][i]: most_similar_frame["type_fes"][i] \
                for i in range(len(most_similar_frame["frame_elements"]))}
        df_srl["type_fes"] = df_srl["role_name_iri"].apply(lambda x: frame_element_to_type[x])

        event_info["srl"] = df_srl
        return event_info

    @staticmethod
    def post_process_output_prompt(output: str) -> str:
        """ Output of prompt in readable csv format """
        output = [x.split(",") for x in output.split("\n") if len(x.split(",")) > 1]
        output = [x[:2]+[",".join(x[2:])] for x in output]
        output = "\n".join(["\t".join(x) for x in output])
        return output


    def __call__(self, events_info: dict) -> dict:
        """ Main """
        events = list(events_info.keys())
        log_errors = defaultdict(int)
        for i in tqdm(range(len(events))):
            event = events[i]
            event_info = events_info[event]

            prompt = self.fill_template(event_info=event_info)

            try:
                output = self.get_completion(prompt=prompt)
                output = self.post_process_output_prompt(output=output)
                print(output)

                if not isinstance(output, NoneType):
                    df_res = pd.read_csv(StringIO(output), sep='\t')
                    events_info[event]["srl"] = df_res
                    events_info[event] = self.update_info(event_info=events_info[event])
                else:
                    events_info[event]["srl"] = None

            except Exception as exception:
                print(f"{event}\t{exception}")
                log_errors[exception] += 1
                events_info[event]["srl"] = f"<ERROR> {exception}"

        return events_info, log_errors


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
    RES, _ = PROMPT_SRL(events_info=EVENTS_INFO)
    LOGGER.log_end()

    with open(args_main["output"], "wb") as openfile:
        pickle.dump(RES, openfile)
