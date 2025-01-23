import os
import lancedb
import pandas as pd
import pyarrow as pa
from typing import Iterator, List, Optional
import random
import tqdm
import json
from .model import BaseEmbeddingModel
from .settings import (
    DB_BATCH_SIZE,
    DATA_SAMPLE_SIZE,
    IMAGE_EXTENSIONS,
    CSV_FILENAME,
    DEFAULT_CSV_BUCKET,
)
import imghdr
from io import BytesIO
from .s3_client import S3Client


def detect_image_type(image_path: str) -> Optional[str]:
    return imghdr.what(image_path)


def find_files_in_path(path, file_extensions=IMAGE_EXTENSIONS) -> Iterator[str]:
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            relative_dir = dirpath.replace(path, "")
            file_path = os.path.join(relative_dir, filename)
            print(file_path)
            if filename.lower().endswith(file_extensions):
                yield file_path
            else:
                absolute_path = os.path.join(dirpath, filename)
                image_type = detect_image_type(absolute_path)
                if f".{image_type}" in file_extensions:
                    yield file_path


def load_images_from_path(data_path: str, sample_size=DATA_SAMPLE_SIZE):
    image_files = list(find_files_in_path(data_path))
    if os.environ['LOAD_DATA'] == "True":
        csv_path = os.environ['CSV_PATH']
        df = pd.read_csv(csv_path)
        image_files = df["image_path"].to_list()
    else:
        print(f"Found {len(image_files)} images in {data_path}")
        if sample_size is not None:
            print(f"Sampling {sample_size} out of {len(image_files)} images...")
            image_files = random.sample(image_files, sample_size)
            csv_path = os.environ['CSV_FILENAME']
            df = pd.read_csv(csv_path)
            image_files = df["image_path"].to_list()
    return image_files, df


def load_images_from_minio(
    data_path: str, S3_Client: S3Client, sample_size=DATA_SAMPLE_SIZE
):
    image_files, df = get_image_files(data_path, S3_Client)
    print(f"Found {len(image_files)} images in {data_path}")
    if sample_size is not None:
        print(f"Sampling {sample_size} out of {len(image_files)} images...")
        image_files = random.sample(image_files, sample_size)
    return image_files, df


def get_image_files(data_path: str, S3_Client: S3Client):
    if CSV_FILENAME:
        print("Getting images from CSV file")
        csv_data = S3_Client.get_obj(DEFAULT_CSV_BUCKET, CSV_FILENAME)
        df = pd.read_csv(BytesIO(csv_data.read()))
        image_files = df["image_path"].to_list()
    elif os.environ.get("CSV_PATH"):
        csv_path = os.environ.get("CSV_PATH")
        print("Getting images from CSV upload by user")
        df = pd.read_csv(csv_path)
        image_files = df["image_path"].to_list()
    else:
        image_files = S3_Client.list_objects_names(data_path)
        df = None

    return image_files, df


def embed_image_files(
    model: BaseEmbeddingModel,
    data_path: str,
    image_paths: List[str],
    S3_Client: Optional[S3Client],
):
    embeddings = []
    for path in image_paths:
        try:
            if isinstance(S3_Client, S3Client):
                image_data = S3_Client.get_obj(data_path, path)
                image_buffer = BytesIO(image_data.read())
                embedding = model.embed_image_path(image_buffer)
            else:
                embedding = model.embed_image_path(
                    image_path=os.path.join(data_path, path)
                )
            embeddings.append((path, embedding))
        except Exception as e:
            print(f"Failed to create embbeding for image {path}.", e)
            embeddings.append((path, None))
    return embeddings


def load_batches(
    db: lancedb.DBConnection,
    table_name: str,
    data_path: str,
    S3_Client: Optional[S3Client],
    model: BaseEmbeddingModel,
    batch_size=DB_BATCH_SIZE,
) -> lancedb.table.Table:
    if isinstance(S3_Client, S3Client):
        image_files, df = load_images_from_minio(data_path, S3_Client)
    else:
        image_files = load_images_from_path(data_path)

    def make_batches() -> Iterator[pa.RecordBatch]:
        with tqdm.tqdm(total=len(image_files)) as progress_bar:
            for i in range(0, len(image_files), batch_size):
                image_paths = image_files[i : i + batch_size]

                results = embed_image_files(model, data_path, image_paths, S3_Client)
                valid_image_paths = [path for path, emb in results if emb is not None]
                valid_embeddings = [emb for path, emb in results if emb is not None]
                valid_title = (
                    df[df["image_path"].isin(valid_image_paths)]["title"]
                    .str.encode("utf-8", errors="replace")
                    .str.decode("utf-8")
                    .tolist()
                )

                image_paths_array = pa.array(valid_image_paths)
                embeddings_array = pa.array(
                    valid_embeddings, pa.list_(pa.float32(), model.dimensions())
                )
                titles_array = pa.array(valid_title)

                progress_bar.update(len(image_paths))

                yield pa.RecordBatch.from_arrays(
                    [
                        titles_array,
                        image_paths_array,
                        embeddings_array,
                    ],
                    [
                        "title",
                        "image_path",
                        "vector",
                    ],
                )

    db_schema = pa.schema(
        [
            pa.field("title", pa.utf8()),
            pa.field("image_path", pa.utf8()),
            pa.field("vector", pa.list_(pa.float32(), model.dimensions())),
        ]
    )
    tbl = db.create_table(
        table_name,
        make_batches(),
        schema=db_schema,
    )
    return tbl


def make_df(
    data_path: str, model: BaseEmbeddingModel, S3_Client: Optional[S3Client]
):
    if S3_Client:
        image_files, df = load_images_from_minio(data_path, S3_Client)
    else:
        print("getting images from local folder")
        image_files, df= load_images_from_path(data_path)

    titles = []
    image_paths = []
    vectors = []
    metadatas = []
    for image_path in tqdm.tqdm(image_files):
        image_path, embedding = embed_image_files(
            model, data_path, [image_path], S3_Client
        )[0]
        if embedding is not None:
            vectors.append(embedding)
            image_paths.append(image_path)
            titles.append(df.loc[df["image_path"] == image_path, "title"].values[0])
            metadatas.append(df.loc[df["image_path"] == image_path, "metadata"].values[0])

    df = pd.DataFrame(
        {
            "title": titles,
            "metadata": metadatas,
            "image_path": image_paths,
            "vector": vectors,
        }
    )
    df['metadata'] = df['metadata'].apply(clean_and_validate_json)
    print(f"Vector: {df['vector']}")
    return df


def load_df(
    db: lancedb.DBConnection,
    table_name: str,
    data_path: str,
    model: BaseEmbeddingModel,
    S3_Client: Optional[S3Client],
) -> lancedb.table.Table:
    return db.create_table(table_name, data=make_df(data_path, model, S3_Client))

def clean_and_validate_json(json_str):
    if pd.notna(json_str):
        try:
            # Try loading the string as JSON to validate it
            json_object = json.loads(json_str)
            return json_object
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None
    else:
        return None
