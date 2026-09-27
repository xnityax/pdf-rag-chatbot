from openai import OpenAI


class OpenAIEmbedder:
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key, timeout=30, max_retries=2)
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        result: list[list[float]] = []
        for start in range(0, len(texts), 64):
            response = self.client.embeddings.create(
                model=self.model, input=texts[start : start + 64], encoding_format="float"
            )
            result.extend(item.embedding for item in sorted(response.data, key=lambda item: item.index))
        return result
