import abc
import numpy as np
from PIL import Image
from transformers import CLIPModel, CLIPProcessor, CLIPTokenizerFast
import torch


# TODO: consider using larger models such as openai/clip-vit-large-patch14
DEFAULT_MODEL_ID = "openai/clip-vit-base-patch32"


class BaseEmbeddingModel(abc.ABC):
    @abc.abstractmethod
    def dimensions(self) -> int:
        pass

    @abc.abstractmethod
    def embed_text(self, query: str) -> np.ndarray:
        pass

    @abc.abstractmethod
    def embed_image(self, image: Image) -> np.ndarray:
        pass

    @abc.abstractmethod
    def embed_image_path(self, image_path: str) -> np.ndarray:
        pass


class ClipModel(BaseEmbeddingModel):
    def __init__(self, model_id=DEFAULT_MODEL_ID) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer: CLIPTokenizerFast = CLIPTokenizerFast.from_pretrained(model_id)
        self.model: CLIPModel = CLIPModel.from_pretrained(model_id).to(self.device)
        self.processor: CLIPProcessor = CLIPProcessor.from_pretrained(model_id)

    def dimensions(self) -> int:
        return 512

    def embed_text(self, query: str) -> np.ndarray:
        try:
            inputs = self.tokenizer([query], padding=True, return_tensors="pt").to(self.device)
            text_features = self.model.get_text_features(**inputs)
        except Exception as e:
            print(f"Error embedding text: {e}")
            return np.zeros(self.dimensions())
        return text_features.detach().cpu().numpy()[0]

    def embed_image(self, image: Image) -> np.ndarray:
        pixel_values = self.processor(images=image, return_tensors="pt")["pixel_values"].to(self.device)
        emb_tensor = self.model.get_image_features(pixel_values)
        return emb_tensor.detach().cpu().numpy()[0]

    def embed_image_path(self, image_path: str) -> np.ndarray:
        return self.embed_image(Image.open(image_path).convert("RGB"))


class RandomMockModel(BaseEmbeddingModel):
    def __init__(self) -> None:
        super().__init__()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dim = 16

    def dimensions(self) -> int:
        return self.dim

    def embed_text(self, query: str) -> np.ndarray:
        return np.random.uniform(size=self.dim)

    def embed_image(self, image: Image) -> np.ndarray:
        return np.random.uniform(size=self.dim)

    def embed_image_path(self, image_path: str) -> np.ndarray:
        return np.random.uniform(size=self.dim)
