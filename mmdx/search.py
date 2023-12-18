import os
import shutil
import tempfile
import lancedb
import pandas as pd
import numpy as np
import duckdb
from typing import Optional, List
from .data_load import load_batches, load_df
from .model import BaseEmbeddingModel
from .db import LabelsDB
from .settings import DEFAULT_TABLE_NAME, DB_BATCH_LOAD, DB_BATCH_SIZE
from .s3_client import S3Client
from io import BytesIO


duckdb.sql(
    """
    INSTALL sqlite;
    LOAD sqlite;
    """
)


class VectorDB:
    def __init__(
        self,
        db_path: str,
        db: lancedb.DBConnection,
        table: lancedb.table.Table,
        model: BaseEmbeddingModel,
        data_path: str,
    ) -> None:
        self.db = db
        self.model = model
        self.tbl = table
        self.data_path = data_path
        self.labelsdb_path = os.path.join(db_path, "labels.db")
        self.labelsdb = LabelsDB(self.labelsdb_path)

    @staticmethod
    def from_data_path(
        data_path: str,
        db_path: str,
        S3_Client: Optional[S3Client],
        model: BaseEmbeddingModel,
        delete_existing: bool = True,
        batch_load: bool = DB_BATCH_LOAD,
        batch_size: int = DB_BATCH_SIZE,
    ):
        db = lancedb.connect(db_path)

        table_name = DEFAULT_TABLE_NAME
        if delete_existing and table_name in db.table_names():
            print(f"Dropping existing database {table_name}...")
            db.drop_table(table_name)
            print("done.")

        if table_name in db.table_names():
            print(f'Opening existing table "{table_name}"...')
            tbl = db.open_table(table_name)
            return VectorDB(db_path, db, tbl, model, data_path)
        else:
            print(f'Creating table "{table_name}"...')
            if batch_load:
                tbl = load_batches(db, table_name, data_path, S3_Client, model, batch_size)
            else:
                tbl = load_df(db, table_name, data_path, model, S3_Client)
            return VectorDB(db_path, db, tbl, model, data_path)

    def count_rows(self) -> int:
        return len(self.tbl)

    def get(self, image_path: str) -> pd.DataFrame:
        lance_tbl = self.tbl.to_lance()
        return duckdb.sql(
            f"SELECT * FROM lance_tbl WHERE image_path='{image_path}';"
        ).to_df()

    def add_label(self, image_path: str, label: str, table: str):
        self.labelsdb.add(image_path=image_path, label=label, table=table)

    def remove_label(self, image_path: str, label: str, table: str):
        self.labelsdb.remove_records(image_path=image_path, label=label, table=table)

    def get_labels(self, table: str, image_path: Optional[str] = None) -> List[str]:
        return self.labelsdb.get(image_path=image_path, table=table)

    def get_label_counts(self) -> dict:
        return self.labelsdb.counts()

    def random_search(self, limit: int) -> pd.DataFrame:
        lance_tbl = self.tbl.to_lance()
        df_hits = duckdb.sql(
            f"""
            SELECT lance_tbl.*, grouped_labels.labels, grouped_labels.types FROM lance_tbl
            LEFT OUTER JOIN (
                SELECT image_path,
                       list(label) AS labels,
                       list(type) AS types
                FROM (
                    SELECT image_path, label, 'description' AS type FROM sqlite_scan('{self.labelsdb_path}', 'description')
                    UNION ALL
                    SELECT image_path, label, 'relevant' AS type FROM sqlite_scan('{self.labelsdb_path}', 'relevant')
                    UNION ALL
                    SELECT image_path, label, 'animal' AS type FROM sqlite_scan('{self.labelsdb_path}', 'animal')
                    UNION ALL
                    SELECT image_path, label, 'keywords' AS type FROM sqlite_scan('{self.labelsdb_path}', 'keywords')
                ) GROUP BY image_path
            ) AS grouped_labels
            ON (lance_tbl.image_path = grouped_labels.image_path)
            USING SAMPLE {limit} ROWS;
        """
        ).to_df()
        df_hits["labels"] = df_hits["labels"].fillna("").apply(list)
        df_hits["title"] = df_hits["title"].fillna("")
        df_hits["types"] = df_hits["types"].fillna("").apply(list)
        df_hits["labels_types_dict"] = df_hits.apply(lambda row: {label: type for label, type in zip(row["labels"], row["types"])}, axis=1)
        df_hits.drop(columns=["vector", "types"], inplace=True)
        print(df_hits["labels_types_dict"])
        return df_hits

    def search_by_image_path(
        self, image_path: str, limit: int, exclude_labeled: bool, S3_Client: Optional[S3Client]
    ) -> pd.DataFrame:
        if S3_Client:
            image_data = S3_Client.get_obj(self.data_path, image_path)
            image = BytesIO(image_data.read())
        else:
            image = os.path.join(self.data_path, image_path)

        image_embedding = self.model.embed_image_path(image)
        df_hits = self.__vector_embedding_search(
            image_embedding,
            limit,
            exclude_image_path=image_path,
            exclude_labeled=exclude_labeled,
        )
        return df_hits

    def search_by_text(
        self, query_string: str, limit: int, exclude_labeled: bool
    ) -> pd.DataFrame:
        query_str_embedding = self.model.embed_text(query=query_string)
        df_hits = self.__vector_embedding_search(
            query_str_embedding, limit, exclude_labeled
        )
        return df_hits

    def __vector_embedding_search(
        self,
        embedding: np.ndarray,
        limit: int,
        exclude_labeled: bool,
        exclude_image_path: str = None,
    ) -> pd.DataFrame:
        if exclude_labeled:
            exclude_image_paths = set(self.labelsdb.get_image_paths())
        else:
            exclude_image_paths = set()

        if exclude_image_path is not None:
            exclude_image_paths.add(exclude_image_path)

        if len(exclude_image_paths) == 0:
            df_hits = self.tbl.search(embedding).limit(limit).to_df()
        else:
            exclude_image_paths_str = ",".join(
                [f"'{image_path}'" for image_path in exclude_image_paths]
            )
            df_hits = (
                self.tbl.search(embedding)
                .where(f"image_path NOT IN ({exclude_image_paths_str})")
                .limit(limit + len(exclude_image_paths))
                .to_df()
            )
            df_hits = df_hits[0:limit]

        df_hits.drop(columns=["vector"], inplace=True)
        df_hits = self.__join_labels(left_table=df_hits)
        return df_hits

    def __join_labels(self, left_table: pd.DataFrame) -> pd.DataFrame:
        df_join = duckdb.sql(
            f"""
            SELECT left_table.*, grouped_labels.labels, grouped_labels.types FROM left_table
            LEFT OUTER JOIN (
                SELECT image_path,
                       list(label) AS labels,
                       list(type) AS types
                FROM (
                    SELECT image_path, label, 'description' AS type FROM sqlite_scan('{self.labelsdb_path}', 'description')
                    UNION ALL
                    SELECT image_path, label, 'relevant' AS type FROM sqlite_scan('{self.labelsdb_path}', 'relevant')
                    UNION ALL
                    SELECT image_path, label, 'animal' AS type FROM sqlite_scan('{self.labelsdb_path}', 'animal')
                    UNION ALL
                    SELECT image_path, label, 'keywords' AS type FROM sqlite_scan('{self.labelsdb_path}', 'keywords')
                ) GROUP BY image_path
            ) AS grouped_labels
            ON (left_table.image_path = grouped_labels.image_path)
            ORDER BY left_table._distance ASC;
        """
        ).to_df()
        df_join["labels"] = df_join["labels"].fillna("").apply(list)
        df_join["types"] = df_join["types"].fillna("").apply(list)
        df_join["title"] = df_join["title"].fillna("")
        df_join["labels_types_dict"] = df_join.apply(lambda row: {label: type for label, type in zip(row["labels"], row["types"])}, axis=1)
        df_join.drop(columns=["types"], inplace=True)
        return df_join

    def create_zip_labeled_binary_data(
            self,
            output_dir: str,
            filename: str) -> str:
        result, column_names = self.labelsdb.create_zip_labeled_data()
        os.makedirs(output_dir, exist_ok=True)
        df = pd.DataFrame(result, columns=column_names)
        original_path = os.environ.get("CSV_PATH")
        original_df = pd.read_csv(original_path)
        original_df = original_df.set_index("image_path")
        cols_to_use = original_df.columns.difference(df.columns)
        # join both
        df = df.join(original_df[cols_to_use], on="image_path")
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "data.csv")
            df.to_csv(csv_path, index=False)

            if output_dir is None:
                output_dir = tempfile.gettempdir()
            if filename.endswith(".zip"):
                zip_path = os.path.join(output_dir, filename)
            else:
                zip_path = os.path.join(output_dir, filename + ".zip")
            shutil.make_archive(zip_path[:-4], "zip", tmpdir)

            return zip_path
