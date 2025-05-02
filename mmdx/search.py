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
import re
import json


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
        # s3_client: Optional[S3Client] = None,
    ) -> None:
        self.db = db
        self.model = model
        self.tbl = table
        self.data_path = data_path
        # self.s3_client = s3_client

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

    def set_label_db(self, project_id: str):
        self.labelsdb_path = os.path.join(f"data/{project_id}", "labels.db")
        self.labelsdb = LabelsDB(self.labelsdb_path)
        self.set_paths(project_id)

    def set_paths(self, project_id):
        self.project_id = project_id
        self.csvpath =f"data/{project_id}/current_sample_training.csv"
        self.hilts_path= f"data/{project_id}/hilts/hilts_sample.json"
        self.hilts_train = f"data/{project_id}/hilts_data.csv"


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

    def random_hilts_search(self, limit: int, s3_client: S3Client) -> pd.DataFrame:
        lance_tbl = self.tbl.to_lance()

        if os.path.exists(self.csvpath):
            hilts_data = {}
            previous = []
            if os.path.exists(self.hilts_path):
                with open(self.hilts_path, "r") as file:
                    hilts_data = json.load(file)
                    previous = hilts_data.keys()

            with open(f"data/{self.project_id}/config_file.json", "r") as f:
                config = json.load(f)
                limit = config["humanLabels"]

            df = pd.read_csv(self.csvpath) # current_sample_training.csv
            # balanced_df = VectorDB.select_balanced_rows(df, limit) ## for demo
            image_paths = []
            if len(hilts_data) >0: # check if first iteration was done
                image_paths = self.select_similar_df(df, hilts_data, s3_client)
                print(f"similarity search: {image_paths}")
            elif image_paths == []:
                image_paths = [path for path in df["image_path"].to_list() if path not in previous]
            image_path_list_str = ', '.join(f"'{path}'" for path in image_paths)


            df_hits = duckdb.sql(
                f"""WITH filtered_data AS (
                    SELECT lance_tbl.*, grouped_labels.labels, grouped_labels.types
                    FROM lance_tbl
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
                    WHERE lance_tbl.image_path IN ({image_path_list_str}))
                    SELECT * FROM filtered_data
                    USING SAMPLE {limit} ROWS;
                    """
                    ).to_df()
            df_hits["labels"] = df_hits["labels"].fillna("").apply(list)
            df_hits["title"] = df_hits["title"].fillna("")
            df_hits["types"] = df_hits["types"].fillna("").apply(list)
            df_hits["animal"] = df_hits.apply(
                lambda row: row["labels"][0] if isinstance(row["labels"], list) and "relevant" in row["types"] else None,
                axis=1
            )
            print(df_hits["labels"])
            print(df_hits["types"])
            df_hits["labels_types_dict"] = df_hits.apply(lambda row: {label: type for label, type in zip(row["labels"], row["types"])}, axis=1)
            df_hits.drop(columns=["vector", "types"], inplace=True)

            for image_path in image_paths:
                if image_path not in hilts_data:
                    hilts_data[image_path] = {}  # You can customize this default structure if needed
                animal_label = df_hits[df_hits["image_path"] == image_path]["animal"].values
                if len(animal_label) > 0:
                    hilts_data[image_path]["llm_label"] = animal_label[0]
            with open(self.hilts_path, "w") as file:
                json.dump(hilts_data, file)
            return df_hits
        else:
            return self.random_search(limit)


    def select_similar_df(self, df: pd.DataFrame, hilts_data: dict, S3_client: S3Client) -> List[str]:
        # remove ads that hilts_data does not have both "human_label" and "llm_label"
        exclude_path = []
        image_paths_include = []
        for image_path in list(hilts_data.keys()):
            if hilts_data[image_path].get("human_label") is None or hilts_data[image_path].get("llm_label") is None:
                exclude_path.append(image_path)
            else:
                image_paths_include.append(image_path)
        image_paths  = []
        for _ , row in df.iterrows(): ## needs to return this paths
            image_path = row["image_path"]
            label = "not animal origin" if row["label"] == 0 else "animal origin"
            exclude_path.append(image_path)
            if S3_client:
                try:
                    image_data = S3_client.get_obj(self.data_path, image_path)
                    image = BytesIO(image_data.read())
                    image_embedding = self.model.embed_image_path(image)
                except Exception as e:
                    print(f"Error loading image {image_path}: {e}")
                    image_embedding = self.model.embed_text(row["title"])
            else:
                image = os.path.join(self.data_path, image_path)
                image_embedding = self.model.embed_image_path(image)
            # Select similar rows based on the vectordb search
            similar = self.vector_embedding_search_hilts(image_embedding, limit=3, include_image_paths=image_paths_include)

            similar["same_label"] = similar.apply(
                lambda row: True if row["animal"] == label else False,
                axis=1
            )
            print("Label: ", label)
            print(similar["animal"])
            # majority vote, similar labels are the same, then use that label
            if similar["same_label"].sum() >= 2:
                print("not opposite label")
                continue
            else:
                image_paths.append(image_path)
                print("opposite label")
        return image_paths

    # @staticmethod
    # def select_balanced_rows(df, limit):
    #     # Split the DataFrame into two subsets based on the "label" column
    #     label_1 = df[df["label"] == 1]
    #     label_0 = df[df["label"] == 0]

    #     # Calculate the number of rows to select from each subset
    #     half_limit = limit // 2

    #     # Select rows from each subset
    #     selected_label_1 = label_1.sample(n=min(half_limit, len(label_1)), random_state=42)
    #     selected_label_0 = label_0.sample(n=min(half_limit, len(label_0)), random_state=42)

    #     # Combine the selected rows
    #     balanced_df = pd.concat([selected_label_1, selected_label_0])

    #     # If the combined DataFrame has fewer rows than the limit, add random samples
    #     remaining_rows = limit - len(balanced_df)
    #     if remaining_rows > 0:
    #         # Exclude already selected rows
    #         remaining_df = df[~df.index.isin(balanced_df.index)]
    #         additional_samples = remaining_df.sample(n=min(remaining_rows, len(remaining_df)), random_state=42)
    #         balanced_df = pd.concat([balanced_df, additional_samples])

    #     # Shuffle the combined DataFrame
    #     balanced_df = balanced_df.sample(frac=1, random_state=42).reset_index(drop=True)

    #     return balanced_df

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
        df_hits["animal"] = df_hits.apply(
            lambda row: row["labels"][0] if isinstance(row["labels"], list) and "relevant" in row["types"] else None,
            axis=1
        )
        df_hits["labels_types_dict"] = df_hits.apply(lambda row: {label: type for label, type in zip(row["labels"], row["types"])}, axis=1)
        df_hits.drop(columns=["vector", "types"], inplace=True)
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
        lance_tbl = self.tbl.to_lance()
        original_path = os.environ.get("CSV_PATH")
        original_df = pd.read_csv(original_path)
        if "description" in original_df.columns:
            original_df['contains_phrase'] = original_df['description'].str.contains(re.escape(query_string), case=False, na=False)
        else:
            original_df['contains_phrase'] = original_df['title'].str.contains(re.escape(query_string), case=False, na=False)

        # Filter DataFrame to include only rows where the phrase is found
        filtered_df = original_df[original_df['contains_phrase']]
        image_path_list = [path for path in filtered_df["image_path"].dropna()]
        image_path_list_str = ', '.join(f"'{path}'" for path in image_path_list)
        print(f"total {image_path_list_str}")
        print(f"list size {limit}")
        df_hits = duckdb.sql(
            f"""WITH filtered_data AS (
                SELECT lance_tbl.*, grouped_labels.labels, grouped_labels.types
                FROM lance_tbl
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
                WHERE lance_tbl.image_path IN ({image_path_list_str}))
                SELECT * FROM filtered_data
                USING SAMPLE {limit} ROWS;
                """
                ).to_df()
        df_hits["labels"] = df_hits["labels"].fillna("").apply(list)
        df_hits["title"] = df_hits["title"].fillna("")
        df_hits["types"] = df_hits["types"].fillna("").apply(list)
        df_hits["animal"] = df_hits.apply(
            lambda row: row["labels"][0] if isinstance(row["labels"], list) and "relevant" in row["types"] else None,
            axis=1
        )
        df_hits["labels_types_dict"] = df_hits.apply(lambda row: {label: type for label, type in zip(row["labels"], row["types"])}, axis=1)
        df_hits.drop(columns=["vector", "types"], inplace=True)
        return df_hits

    def search_by_seller(
        self, query_string: str, limit: int, exclude_labeled: bool
    ) -> pd.DataFrame:
        lance_tbl = self.tbl.to_lance()
        original_path = os.environ.get("CSV_PATH")
        original_df = pd.read_csv(original_path)
        original_df =  original_df[original_df["seller"]==query_string]
        image_path_list = [path for path in original_df["image_path"].dropna()]
        image_path_list_str = ', '.join(f"'{path}'" for path in image_path_list)

        df_hits = duckdb.sql(
            f"""WITH filtered_data AS (
                SELECT lance_tbl.*, grouped_labels.labels, grouped_labels.types
                FROM lance_tbl
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
                WHERE lance_tbl.image_path IN ({image_path_list_str}))
                SELECT * FROM filtered_data
                USING SAMPLE {limit} ROWS;
                """
        ).to_df()
        df_hits["labels"] = df_hits["labels"].fillna("").apply(list)
        df_hits["title"] = df_hits["title"].fillna("")
        df_hits["types"] = df_hits["types"].fillna("").apply(list)
        df_hits["animal"] = df_hits.apply(
            lambda row: row["labels"][0] if isinstance(row["labels"], list) and "relevant" in row["types"] else None,
            axis=1
        )
        df_hits["labels_types_dict"] = df_hits.apply(lambda row: {label: type for label, type in zip(row["labels"], row["types"])}, axis=1)
        df_hits.drop(columns=["vector", "types"], inplace=True)
        return df_hits

    def vector_embedding_search_hilts(
        self,
        embedding: np.ndarray,
        limit: int,
        include_image_paths: List[str] = [],
    ) -> pd.DataFrame:
        # Handle empty include_image_paths
        if include_image_paths:
            image_path_include_list_str = ', '.join(f"'{path}'" for path in include_image_paths)
            include_clause = f"image_path IN ({image_path_include_list_str})"
            print(include_clause)
        else:
            include_clause = "1=1"  # Always true, effectively no inclusion filter

        df_hits = (
            self.tbl.search(embedding)
            .where(include_clause,  prefilter=True)
            .limit(limit)
            .to_df()
        )

        df_hits = df_hits[0:limit]

        df_hits.drop(columns=["vector"], inplace=True)
        df_hits = self.__join_labels(left_table=df_hits)
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
        df_join["animal"] = df_join.apply(
            lambda row: row["labels"][0] if isinstance(row["labels"], list) and "relevant" in row["types"] else None,
            axis=1
        )
        df_join["labels_types_dict"] = df_join.apply(lambda row: {label: type for label, type in zip(row["labels"], row["types"])}, axis=1)
        df_join.drop(columns=["types"], inplace=True)
        return df_join

    def search_labeled_data(self, limit):
        image_path = set(self.labelsdb.get_image_paths())
        lance_tbl = self.tbl.to_lance()
        image_path_condition = ", ".join([f"'{path}'" for path in image_path])

        df_hits = duckdb.sql(
            f"""
            SELECT lance_tbl.*, grouped_labels.labels, grouped_labels.types
            FROM lance_tbl
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
            WHERE lance_tbl.image_path IN ({image_path_condition})
        """
        ).to_df()
        df_hits["labels"] = df_hits["labels"].fillna("").apply(list)
        df_hits["title"] = df_hits["title"].fillna("")
        df_hits["types"] = df_hits["types"].fillna("").apply(list)
        df_hits["animal"] = df_hits.apply(
            lambda row: row["labels"][0] if isinstance(row["labels"], list) and "relevant" in row["types"] else None,
            axis=1
        )
        df_hits["labels_types_dict"] = df_hits.apply(lambda row: {label: type for label, type in zip(row["labels"], row["types"])}, axis=1)
        df_hits.drop(columns=["vector", "types"], inplace=True)
        print(df_hits["labels_types_dict"])
        return df_hits

    def create_zip_labeled_binary_data(
            self,
            output_dir: str,
            filename: str) -> str:
        result, column_names = self.labelsdb.create_labeled_data()
        os.makedirs(output_dir, exist_ok=True)
        df = pd.DataFrame(result, columns=column_names)
        original_path = os.environ.get("CSV_PATH")
        original_df = pd.read_csv(original_path)
        original_df = original_df.set_index("image_path")
        cols_to_use = df.columns.difference(original_df.columns)
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


    def create_hilts_data(self) -> str:
        result, column_names = self.labelsdb.create_labeled_data()
        df = pd.DataFrame(result, columns=column_names)
        # df.to_csv(f"data/{dirc}/labeled.csv")
        original_df = pd.read_csv(self.csvpath)
        original_df = original_df.set_index("image_path")
        cols_to_use = df.columns.difference(original_df.columns)
        # join both
        original_df = original_df.join(df[cols_to_use].set_index("image_path"))
        original_df["relevant_"] = np.where(original_df["relevant"] == "not animal origin", 0,1)
        original_df["relevant_"] = np.where(original_df["relevant"].isnull(), None, original_df["relevant_"])
        original_df["label"] = np.where(original_df["relevant_"].isnull(), original_df["label"], original_df["relevant_"])
        original_df["animal"] = original_df["relevant"]

        original_df.drop(columns=["relevant_", "relevant"], inplace=True)
        original_df = original_df.reset_index()
        original_df.to_csv(self.hilts_train, index=False)

        ## STATS LOGS
        if os.path.exists(self.hilts_path):
            with open(self.hilts_path, "r") as file:
                hilts_data = json.load(file)
            for image_path in hilts_data.keys():
                animal_label = original_df[original_df["image_path"] == image_path]["animal"].values
                if len(animal_label) > 0:
                    hilts_data[image_path]["human_label"] = animal_label[0]

            with open(self.hilts_path, "w") as file:
                json.dump(hilts_data, file)

