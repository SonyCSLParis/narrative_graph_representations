"""
Clustering frames with their labels
Useful references
- sentence-transformers: https://huggingface.co/sentence-transformers/bert-base-nli-mean-tokens
"""
# -*- coding: utf-8 -*-
import os
import argparse
from bertopic import BERTopic
from hdt import HDTDocument
from sentence_transformers import SentenceTransformer
from framester.query import get_frames

MODEL = SentenceTransformer('sentence-transformers/bert-base-nli-mean-tokens')


def get_frame_label(label):
    """ Readable frame label """
    return label.split("/")[-1].lower().replace('_', " ")

def cluster_frames(doc, output_folder):
    """ Main """
    frames = get_frames(hdt_doc=doc)
    labels = [get_frame_label(label=x) for x in frames]
    topic_model = BERTopic(representation_model=MODEL)
    topic_model.fit_transform(labels)

    topic_model.get_topic_info().to_csv(os.path.join(output_folder, "frames_topic_info.csv"))
    topic_model.get_document_info(labels) \
        .to_csv(os.path.join(output_folder, "frames_document_info.csv"))


if __name__ == '__main__':
    # python framester/cluster_frames.py -hdt ../framester_melis/framester/hdt -o data/framester
    ap = argparse.ArgumentParser()
    ap.add_argument('-hdt', "--hdt", required=True,
                    help="hdt path to get frames")
    ap.add_argument('-o', "--output", required=True,
                    help="folder_output")
    args_main = vars(ap.parse_args())

    DOC = HDTDocument(args_main["hdt"])
    cluster_frames(doc=DOC, output_folder=args_main["output"])
