import mmdx.settings
from mmdx.model import ClipModel
import os
from mmdx.search import VectorDB
from mmdx.s3_client import S3Client

from dotenv import load_dotenv
load_dotenv()

from mmdx.settings import (
    DATA_PATH,
    DB_PATH,
    DB_DELETE_EXISTING,
    DB_BATCH_LOAD,
    ACCESS_KEY,
    ENDPOINT_URL,
    SECRET_KEY,
    DATA_SOURCE,
)

def create_db_for_data_path():
    data_path = DATA_PATH
    db_path = DB_PATH

    if DATA_SOURCE.upper() == "S3":
        S3_Client = S3Client(
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY,
            endpoint_url=ENDPOINT_URL,
        )
        print("created S3 CLIENT")
        print(f"access: {ACCESS_KEY}")
    else:
        S3_Client=None
        data_path = DATA_PATH
        db_path = DB_PATH

    if DATA_SOURCE.upper() == "S3":
        data_path_msg = f" - Data Bucket: {data_path}"
    else:
        S3_Client = None
        data_path_msg = f" - Raw data path: {os.path.abspath(data_path)}"

    print("Loading embedding model...")
    model = ClipModel()

    print(f"Loading vector database:")
    print(f" - DB path: {os.path.abspath(db_path)}")
    print(data_path_msg)
    print(f" - Delete existing?: {DB_DELETE_EXISTING}")
    print(f" - Batch load?: {DB_BATCH_LOAD}")
    vectordb = VectorDB.from_data_path(
        data_path,
        db_path,
        S3_Client,
        model,
        delete_existing=DB_DELETE_EXISTING,
        batch_load=DB_BATCH_LOAD,
    )
    print("Finished DB initialization.")





