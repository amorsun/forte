# Copyright 2019 The Forte Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pylint: disable=attribute-defined-outside-init
from typing import Dict, Any

from texar.torch.hyperparams import HParams

from forte.common.resources import Resources
from forte.data import DataPack, MultiPack
from forte.data.ontology import Query
from forte.processors.base import MultiPackProcessor
from forte.indexers import ElasticSearchIndexer

from ft.onto.base_ontology import Document

__all__ = [
    "ElasticSearchProcessor"
]


class ElasticSearchProcessor(MultiPackProcessor):
    r"""This processor searches for relevant documents for a query"""

    # pylint: disable=useless-super-delegation
    def __init__(self) -> None:
        super().__init__()

    def initialize(self, resources: Resources, configs: HParams):

        self.resources = resources
        self.config = configs
        self.index = ElasticSearchIndexer(hparams=self.config.index_config)

    @staticmethod
    def default_hparams() -> Dict[str, Any]:
        return {
            "query_pack_name": "query",
            "index_config": ElasticSearchIndexer.default_hparams(),
            "field": "content"
        }

    def _process(self, input_pack: MultiPack):
        query_pack = input_pack.get_pack(self.config.query_pack_name)
        first_query = list(query_pack.get_entries(Query))[0]
        results = self.index.search(first_query.value)
        hits = results["hits"]["hits"]
        packs = {}
        for idx, hit in enumerate(hits):
            pack = DataPack()
            document = hit["_source"]
            content = document[self.config.field]
            # TODO: add the BM score and the labels for retrieved documents
            # which will be used by the reranker
            # Convert `Document` to `Passage`
            document = Document(pack=pack, begin=0, end=len(content))
            pack.add_entry(document)
            pack.set_text(content)
            packs[f"{self.config.response_pack_name_prefix}_{idx}"] = pack

        input_pack.update_pack(packs)
