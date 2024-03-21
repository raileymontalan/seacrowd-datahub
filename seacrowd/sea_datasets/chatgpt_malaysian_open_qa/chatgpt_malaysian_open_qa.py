# coding=utf-8
# Copyright 2022 The HuggingFace Datasets Authors and the current dataset script contributor.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from pathlib import Path
from typing import Dict, List, Tuple

import datasets

from seacrowd.utils import schemas
from seacrowd.utils.configs import SEACrowdConfig
from seacrowd.utils.constants import Licenses, Tasks

_CITATION = """\
@article{malaysian-dataset,
  title = {Malaysian-Dataset},
  url = {https://github.com/mesolitica/malaysian-dataset},
}
"""

_DATASETNAME = "chatgpt_malaysian_open_qa"

_DESCRIPTION = """\
This is a synthetic Malaysian Open QA dataset generated using ChatGPT3.5 on MS Wikipedia, MS Common Crawl, and Malaysia Hansard.
Subsets include `common-crawl-qa` (69k rows), `hansard-qa` (42k rows), and `wikipedia-qa` (44k rows).
"""

_HOMEPAGE = "https://huggingface.co/datasets/mesolitica/chatgpt-malaysian-open-qa"

_LANGUAGES = ["zlm"]

_LICENSE = Licenses.CC_BY_NC_2_0.value

_LOCAL = False

_URLS = {
    "common_crawl_qa": "https://huggingface.co/datasets/mesolitica/chatgpt-malaysian-open-qa/resolve/main/common-crawl-qa.jsonl",
    "hansard_qa": "https://huggingface.co/datasets/mesolitica/chatgpt-malaysian-open-qa/resolve/main/hansard-qa.jsonl",
    "wikipedia_qa": "https://huggingface.co/datasets/mesolitica/chatgpt-malaysian-open-qa/resolve/main/wikipedia-qa.jsonl",
}

_SUPPORTED_TASKS = [Tasks.QUESTION_ANSWERING]

_SOURCE_VERSION = "1.0.0"

_SEACROWD_VERSION = "1.0.0"


class ChatGPTMalaysianOpenQADataset(datasets.GeneratorBasedBuilder):
    """
    ChatGPT Malaysian Open QA Dataset is a Malaysian QA dataset from https://huggingface.co/datasets/mesolitica/chatgpt-malaysian-open-qa.
    """

    SOURCE_VERSION = datasets.Version(_SOURCE_VERSION)
    SEACROWD_VERSION = datasets.Version(_SEACROWD_VERSION)

    BUILDER_CONFIGS = [
        SEACrowdConfig(
            name=f"{_DATASETNAME}_{subset}_source",
            version=datasets.Version(_SOURCE_VERSION),
            description=f"{_DATASETNAME}_{subset} source schema",
            schema="source",
            subset_id=f"{_DATASETNAME}_{subset}",
        )
        for subset in _URLS.keys()
    ] + [
        SEACrowdConfig(
            name=f"{_DATASETNAME}_{subset}_seacrowd_qa",
            version=datasets.Version(_SEACROWD_VERSION),
            description=f"{_DATASETNAME}_{subset} SEACrowd schema",
            schema="seacrowd_qa",
            subset_id=f"{_DATASETNAME}_{subset}",
        )
        for subset in _URLS.keys()
    ]

    def _info(self) -> datasets.DatasetInfo:
        if self.config.schema == "source" and "wikipedia_qa" not in self.config.subset_id:
            features = datasets.Features(
                {
                    "paragraph": datasets.Value("string"),
                    "qa": datasets.Value("string"),
                }
            )
        elif self.config.schema == "source" and "wikipedia_qa" in self.config.subset_id:
            features = datasets.Features(
                {
                    "paragraph": datasets.Value("string"),
                    "qa": datasets.Value("string"),
                    "url": datasets.Value("string"),
                }
            )
        elif self.config.schema == "seacrowd_qa":
            features = schemas.qa_features
        else:
            raise ValueError(f"Invalid schema: '{self.config.schema}'")

        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=features,
            homepage=_HOMEPAGE,
            license=_LICENSE,
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager: datasets.DownloadManager) -> List[datasets.SplitGenerator]:
        """
        Returns SplitGenerators.
        """
        start = len(_DATASETNAME) + 1
        url = _URLS[self.config.subset_id[start:]]
        path = dl_manager.download_and_extract(url)

        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={
                    "filepath": path,
                    "split": "train",
                },
            )
        ]

    def _generate_examples(self, filepath: Path, split: str) -> Tuple[int, Dict]:
        """
        Yields examples as (key, example) tuples.
        """

        idx = 0
        with open(filepath, "r") as f:
            data = list(map(json.loads, f))
            if self.config.schema == "source":
                for d in data:
                    x = {k: v if v != "" and k in self.info.features else None for k, v in d.items()}
                    if "wikipedia_qa" in self.config.subset_id:
                        x["url"] = d["url"]
                    yield idx, x
                    idx += 1
            elif self.config.schema == "seacrowd_qa":
                for d in data:
                    for q in d["qa"]["qa"]:
                        x = {
                            "id": idx,
                            "question_id": idx,
                            "document_id": idx,
                            "question": q["question"],
                            "type": "extractive",
                            "choices": [],
                            "context": d["paragraph"],
                            "answer": [q["answer"]],
                            "meta": {},
                        }
                        yield idx, x
                        idx += 1
            else:
                raise ValueError(f"Invalid schema: '{self.config.schema}'")
