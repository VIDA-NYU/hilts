#!/usr/bin/env python
"""Tests for `mmdx` package."""
import pandas as pd
import os
from mmdx.db import LabelsDB
from mmdx.data_load import find_files_in_path
from mmdx.search import VectorDB
from mmdx.model import ClipModel, RandomMockModel
from mmdx.s3_client import S3Client
from io import BytesIO
import duckdb
import lancedb


# data_path = "client/public/test-img-dataset"
## read from .env
from dotenv import load_dotenv
load_dotenv()
# Load environment variables from .env file
data_path = os.getenv("DATA_PATH")
s3_client = S3Client(access_key=os.getenv("ACCESS_KEY"),
                        secret_key=os.getenv("SECRET_KEY"),
                        endpoint_url=os.getenv("ENDPOINT_URL"))


# def test():
#     model = ClipModel()

#     db = VectorDB.from_data_path(data_path, os.getenv("DB_PATH"), s3_client, model, delete_existing=False, batch_load=False)

#     lance_tbl: lancedb.table.Table = db.tbl

#     image_data = s3_client.get_obj(data_path, "04acb177-8fcd-4c78-99a2-4c1a5e41695d.png")
#     image = BytesIO(image_data.read())
#     image_embedding = model.embed_image_path(image)


#     # images = [
#     #     'e26eb2fa-214f-4479-8ab0-15aef342ae21.png',
#     #     'f1eb0bdb-ede4-4b1e-a6b8-ce58528a3a03.png',
#     #     'e5b221e8-d288-428b-b712-bc5a2f9fb39d.png',
#     #     '7f797ac9-7c51-4580-84d9-d4d31e39ecd6.png',
#     #     '9501712b-e4f0-4c99-9dd6-12650193e836.png']
#     # result = tbl.search([0.5, 0.2]).where("id = 10", prefilter=True).limit(1).to_arrow()
#     df = lance_tbl.search(image_embedding).where('image_path = "e26eb2fa-214f-4479-8ab0-15aef342ae21.png"', prefilter=True).to_df()
#     # df = lance_tbl.where('image_path = "e26eb2fa-214f-4479-8ab0-15aef342ae21.png"')



#     # print( df[['image_path']] )
#     print(df)

    # print(image_embedding.shape)



    # self.tbl.search(embedding)
    #     .where(f"image_path NOT IN ({exclude_image_paths_str})")
    #     .limit(limit + len(exclude_image_paths))
    #     .to_df()

def test_similarity_search():
    model = ClipModel()
    db = VectorDB.from_data_path(data_path, os.getenv("DB_PATH"), s3_client, model, delete_existing=False, batch_load=False)
    assert db != None
    db.set_label_db("test")
    images = ['e26eb2fa-214f-4479-8ab0-15aef342ae21.png', 'f1eb0bdb-ede4-4b1e-a6b8-ce58528a3a03.png', 'e5b221e8-d288-428b-b712-bc5a2f9fb39d.png', '7f797ac9-7c51-4580-84d9-d4d31e39ecd6.png', '9501712b-e4f0-4c99-9dd6-12650193e836.png']
    for image_path in images:
        db.add_label(image_path, "animal origin", "relevant")

    image_data = s3_client.get_obj(data_path, "04acb177-8fcd-4c78-99a2-4c1a5e41695d.png")
    image = BytesIO(image_data.read())
    image_embedding = model.embed_image_path(image)


    df = db.vector_embedding_search_hilts(image_embedding, limit=2, include_image_paths=images)
    print(df)

def test_create_vector_from_path_and_search(tmp_path):
    db_path = tmp_path / "test_create_vector_from_path_and_search"
    model = RandomMockModel()
    db = VectorDB.from_data_path(data_path, db_path,s3_client, model)
    assert db != None

    hits = db.search_by_text("example query", limit=3)
    assert len(hits.index) == 3

    hits = db.search_by_text("example query", limit=5)
    assert len(hits.index) == 5

    assert isinstance(hits, pd.DataFrame)


# def test_random_search(tmp_path):
#     db_path = tmp_path / "test_random_search"
#     model = RandomMockModel()
#     db = VectorDB.from_data_path(data_path, db_path, model)
#     assert db != None

#     hits = db.random_search(limit=3)
#     assert len(hits.index) == 3

#     hits = db.random_search(limit=6)
#     assert len(hits.index) == 6


# def test_image_search(tmp_path):
#     db_path = tmp_path / "test_image_search"
#     model = RandomMockModel()
#     db = VectorDB.from_data_path(data_path, db_path, model)
#     assert db != None

#     # first, retrieve a random image to use as query
#     hits = db.random_search(limit=1)
#     assert len(hits.index) == 1

#     # run actual image search using the random image as query
#     random_query_path = hits.iloc[0]["image_path"]
#     hits = db.search_by_image_path(random_query_path, limit=5)
#     # make sure we get exactly 5 results
#     assert len(hits.index) == 5
#     # make sure the query image is not in the results
#     assert hits["image_path"].eq(random_query_path).any() == False


# # def test_make_batches():
# #     image_files = list(find_files_in_path(data_path))
# #     model = RandomMockModel()
# #
# #     chuck_count = 0
# #     total_count = 0
# #     for df in make_batches(data_path, image_files, model, batch_size=3):
# #         assert df.num_rows == 3
# #         chuck_count += 1
# #         total_count += df.num_rows
# #
# #     assert chuck_count == 4
# #     assert total_count == len(image_files)


# def test_load_db_dataframe(tmp_path):
#     db_path = tmp_path / "test_load_db_dataframe"
#     model = RandomMockModel()
#     image_files = list(find_files_in_path(data_path))

#     db = VectorDB.from_data_path(
#         data_path, db_path, model, delete_existing=True, batch_load=False, batch_size=3
#     )

#     total_count = db.count_rows()
#     assert total_count == len(image_files)


# def test_load_db_in_batches(tmp_path):
#     db_path = tmp_path / "test_load_db_in_batches"
#     model = RandomMockModel()
#     image_files = list(find_files_in_path(data_path))

#     db = VectorDB.from_data_path(
#         data_path, db_path, model, delete_existing=True, batch_load=True
#     )

#     total_count = db.count_rows()
#     assert total_count == len(image_files)


# def test_add_and_query_labels(tmp_path):
#     db_path = tmp_path / "test_add_and_query_labels"

#     model = RandomMockModel()
#     db = VectorDB.from_data_path(data_path, db_path, model)
#     assert db != None

#     # first, retrieve a random image to use as query
#     hits = db.random_search(limit=2)
#     assert len(hits.index) == 2

#     random_query_path_1 = hits.iloc[0]["image_path"]
#     random_query_path_2 = hits.iloc[1]["image_path"]

#     # initially, images should have no labels
#     labels = db.get_labels(image_path=random_query_path_1)
#     assert labels == []
#     assert len(labels) == 0

#     # when we add one label, get_labels must return it
#     db.add_label(image_path=random_query_path_1, label="label_1")
#     assert db.get_labels(image_path=random_query_path_1) == ["label_1"]
#     assert db.get_labels(image_path=random_query_path_2) == []

#     # when we add another label, get_labels must return all of them
#     db.add_label(image_path=random_query_path_1, label="label_2")
#     assert db.get_labels(image_path=random_query_path_1) == ["label_1", "label_2"]
#     assert db.get_labels(image_path=random_query_path_2) == []

#     db.add_label(image_path=random_query_path_2, label="label_1_query2")
#     assert db.get_labels(image_path=random_query_path_1) == ["label_1", "label_2"]
#     assert db.get_labels(image_path=random_query_path_2) == ["label_1_query2"]

#     # run a random search and verify we returned all items in the database
#     # assumption: less than 100 items in the test dataset
#     hits = db.random_search(limit=100)
#     assert set(hits.columns) == set(["image_path", "labels"])
#     assert len(hits.index) == db.count_rows()

#     # given that labels were added, random search must return labels as well
#     search_result = hits[hits["image_path"] == random_query_path_1].copy().reset_index()
#     assert len(search_result.index) == 1
#     assert search_result.loc[0]["image_path"] == random_query_path_1
#     assert search_result.loc[0]["labels"] == ["label_1", "label_2"]

#     # Check that search by image also returns the labels.
#     # Assumptions:
#     # - Less than 100 items in the test dataset
#     # - Searching by random_query_path_2 will always return return random_query_path
#     #   anyway due to the large number of requested results
#     hits = db.search_by_image_path(image_path=random_query_path_2, limit=100)
#     assert set(["image_path", "labels"]).issubset(set(hits.columns))
#     # we subtract 1 as it must not include the query
#     assert len(hits.index) == db.count_rows() - 1

#     # search by image path must return labels as well
#     search_result = hits[hits["image_path"] == random_query_path_1].copy().reset_index()
#     assert len(search_result.index) == 1
#     assert search_result.loc[0]["image_path"] == random_query_path_1
#     assert search_result.loc[0]["labels"] == ["label_1", "label_2"]

#     # items that do not have labels must return an empty array
#     search_result = hits[hits["image_path"] != random_query_path_1].copy().reset_index()
#     assert len(search_result.index) == db.count_rows() - 2
#     assert search_result.loc[0]["image_path"] != random_query_path_1
#     assert search_result.loc[0]["labels"] == []

#     hits = db.search_by_text(query_string="some random query str", limit=100)
#     assert set(["image_path", "labels"]).issubset(set(hits.columns))
#     assert len(hits.index) == db.count_rows()

#     # search by keyword embedding must return labels as well
#     search_result = hits[hits["image_path"] == random_query_path_1].copy().reset_index()
#     assert len(search_result.index) == 1
#     assert search_result.loc[0]["image_path"] == random_query_path_1
#     assert search_result.loc[0]["labels"] == ["label_1", "label_2"]

#     search_result = hits[hits["image_path"] == random_query_path_2].copy().reset_index()
#     assert search_result.loc[0]["image_path"] == random_query_path_2
#     assert search_result.loc[0]["labels"] == ["label_1_query2"]

#     # items that do not have labels must return an empty array
#     search_result = (
#         hits[~hits["image_path"].isin([random_query_path_1, random_query_path_2])]
#         .copy()
#         .reset_index()
#     )
#     assert len(search_result.index) == db.count_rows() - 2
#     assert search_result.loc[0]["labels"] == []

#     # when we remove the label, get_labels must NOT return it
#     assert db.get_labels(image_path=random_query_path_1) == ["label_1", "label_2"]

#     db.remove_label(image_path=random_query_path_1, label="label_1")
#     assert db.get_labels(image_path=random_query_path_1) == ["label_2"]

#     db.remove_label(image_path=random_query_path_1, label="label_2")
#     assert db.get_labels(image_path=random_query_path_1) == []


# def test_label_db():
#     """
#     Tests adding and removing labels to the LabelDB.
#     """
#     db_file = "data/test/db_label_test/labels.db"

#     if os.path.exists(db_file):
#         os.remove(db_file)
#         print(f"Removed existing DB file: {db_file}")
#     os.makedirs(os.path.dirname(db_file), exist_ok=True)

#     db = LabelsDB(db_file=db_file)

#     assert db != None
#     assert db.get() == []

#     db.add(image_path="image_1", label="label_1")
#     assert set(db.get()) == set(["label_1"])
#     assert set(db.get(image_path="image_1")) == set(["label_1"])
#     assert set(db.get(image_path="image_2")) == set([])

#     db.add(image_path="image_1", label="label_2")
#     assert set(db.get()) == set(["label_1", "label_2"])
#     assert set(db.get(image_path="image_1")) == set(["label_1", "label_2"])
#     assert set(db.get(image_path="image_2")) == set([])

#     db.add(image_path="image_2", label="label_1")
#     assert set(db.get()) == set(["label_1", "label_2"])
#     assert set(db.get(image_path="image_1")) == set(["label_1", "label_2"])
#     assert set(db.get(image_path="image_2")) == set(["label_1"])

#     db.add(image_path="image_2", label="label_3")
#     assert set(db.get()) == set(["label_1", "label_2", "label_3"])
#     assert set(db.get(image_path="image_1")) == set(["label_1", "label_2"])
#     assert set(db.get(image_path="image_2")) == set(["label_1", "label_3"])

#     db.remove(image_path="image_1", label="label_1")
#     assert set(db.get()) == set(["label_1", "label_2", "label_3"])
#     assert set(db.get(image_path="image_1")) == set(["label_2"])
#     assert set(db.get(image_path="image_2")) == set(["label_1", "label_3"])

#     db.remove(image_path="image_1", label="label_2")
#     assert set(db.get()) == set(["label_1", "label_3"])
#     assert set(db.get(image_path="image_1")) == set([])
#     assert set(db.get(image_path="image_2")) == set(["label_1", "label_3"])

#     label_counts = db.counts()
#     assert label_counts['label_1'] == 1
#     assert label_counts['label_3'] == 1
