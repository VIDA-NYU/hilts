import os
from dotenv import load_dotenv
from typing import Optional, Tuple

res = load_dotenv()  # take environment variables from .env.
print(f"env {res}")
print(os.getenv("DB_DELETE_EXISTING"))


def parse_image_extensions(value: Optional[str], default: tuple) -> tuple:
    if value is None or value.strip() == "":
        return default
    else:
        return tuple([f".{ext.strip().strip('.')}" for ext in value.split(",")])


def parse_int(value: Optional[str], default: Optional[int] = None) -> Optional[int]:
    if value is None or value.strip() == "":
        return default
    else:
        try:
            return int(value)
        except ValueError:
            return None


IMAGE_EXTENSIONS: Tuple[str, ...] = parse_image_extensions(
    os.getenv("IMAGE_EXTENSIONS"),
    default=(".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"),
)

DATA_SOURCE: str = os.getenv("DATA_SOURCE", default="S3")
DATA_PATH: str = os.getenv("DATA_PATH", default=None) #default="data/leather_images/")
DB_PATH: str = os.getenv("DB_PATH", default="data/db/")
DB_DELETE_EXISTING: bool = str(os.getenv("DB_DELETE_EXISTING")).lower() == "true"
DB_BATCH_LOAD: bool = str(os.getenv("DB_BATCH_LOAD")).lower() == "true"
DB_BATCH_SIZE: int = int(os.getenv("DB_BATCH_SIZE", default=16))
DEFAULT_TABLE_NAME: str = "images"
DATA_SAMPLE_SIZE: Optional[int] = parse_int(os.getenv("DATA_SAMPLE_SIZE"))
ACCESS_KEY: str = os.getenv("ACCESS_KEY", default=None)
SECRET_KEY: str = os.getenv("SECRET_KEY", default=None)
ENDPOINT: str = os.getenv("ENDPOINT", default=None)
ENDPOINT_URL: str = os.getenv("ENDPOINT_URL", default=None)
DEFAULT_CSV_BUCKET: str = "labeling-csv"
CSV_FILENAME: str = os.getenv("CSV_FILENAME", default=None)
LOAD_DATA: bool = str(os.getenv("LOAD_DATA")).lower() == "true"
DEMO: bool = str(os.getenv("DEMO")).lower() == "true"


