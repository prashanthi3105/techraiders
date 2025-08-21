seafch

import os, json
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

class SearchClientWrapper:
    def __init__(self, endpoint, key):
        self.client = SearchClient(endpoint, "swissre-docs", AzureKeyCredential(key))
        openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        openai_key      = os.getenv("AZURE_OPENAI_KEY")
        if openai_endpoint and openai_key:
            self.oai = AzureOpenAI(azure_endpoint=openai_endpoint,
                                   api_key=openai_key,
                                   api_version="2024-05-01-preview")
        else:
            self.oai = None

    def find_similar(self, text: str, top=3):
        if not self.oai:
            return []
        # text-embedding-3-small
        emb = self.oai.embeddings.create(input=text, model="text-embedding-3-small").data[0].embedding
        results = self.client.search(search_text="*", vector_queries=[{
            "vector": emb,
            "k": top,
            "fields": "contentVector"
        }])
        return [json.dumps({"text": r["content"][:200]}) for r in results]