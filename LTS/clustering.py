import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
import os

class TextClustering:
    def __init__(self, data, text_column="title", n_cluster=5, algorithm="kmeans", project_id="default"):
        """
        Initializes the clustering object with the dataset and the name of the text column.
        """
        self.data = data
        self.text_column = text_column
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.X = None
        self.algorithm = algorithm
        self.n_cluster = n_cluster
        self.project_id = project_id
        self.filename = "filename" + "_cluster_data"

    def preprocess_text(self):
        """
        Converts the text column to a numerical format using TF-IDF vectorization.
        """
        self.X = self.vectorizer.fit_transform(self.data[self.text_column])
        print(f"Preprocessed text data into shape: {self.X.shape}")

    def perform_kmeans(self):
        """
        Performs KMeans clustering on the text data.
        """
        n_clusters = self.n_cluster
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(self.X)
        self.data['label_cluster'] = kmeans.labels_.astype(int)
        self.save_csv(self.filename, self.data)
        print(f"KMeans clustering complete with {n_clusters} clusters.")
        return self.data

    def perform_agglo(self):
        """
        Performs Agglomerative Clustering on the text data.
        """
        n_clusters = self.n_cluster
        agglo = AgglomerativeClustering(n_clusters=n_clusters)
        agglo_labels = agglo.fit_predict(self.X.toarray())  # AgglomerativeClustering needs dense array input
        self.data['label_cluster'] = int(agglo_labels)
        self.save_csv(self.filename, self.data)
        print(f"Agglomerative Clustering complete with {n_clusters} clusters.")
        return self.data

    def perform_gmm(self):
        """
        Performs Gaussian Mixture Model clustering on the text data.
        """
        gmm = GaussianMixture(n_components=self.n_cluster, random_state=42)
        gmm_labels = gmm.fit_predict(self.X.toarray())  # GMM also works better with dense arrays
        self.data['label_cluster'] =int(gmm_labels)
        self.save_csv(self.filename, self.data)
        print(f"GMM clustering complete with {self.n_cluster} clusters.")
        return self.data


    def perform_lda(self):
        """
        Perform Latent Dirichlet Allocation (LDA) topic modeling on the text data.
        This method assigns a dominant topic to each document.
        """
        # lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
        # lda.fit(self.X)
        # lda_topics = lda.transform(self.X)
        # # Assign the most dominant topic for each document
        # self.data['topic_label'] = np.argmax(lda_topics, axis=1)
        # print(f"LDA topic modeling complete with {n_topics} topics.")
        # return self.data
        from .lda import LDATopicModel  # Import here to avoid circular imports
        lda_topic_model = LDATopicModel(num_topics=int(self.n_cluster))
        topics = lda_topic_model.fit_transform(self.data[self.text_column].to_list())
        self.data["label_cluster"] = [int(topic) for topic in topics]
        self.save_csv(self.filename, self.data)
        print("LDA created")
        return self.data

    def perform_clustering(self, ):
        """
        Perform the specified clustering algorithm with provided parameters.
        """
        if self.algorithm == "kmeans":
            return self.perform_kmeans()
        elif self.algorithm == "agglo":
            return self.perform_agglo()
        elif self.algorithm == "gmm":
            return self.perform_gmm()
        elif self.algorithm == "lda":
            return self.perform_lda()
        else:
            raise ValueError("Unknown algorithm. Please choose from 'agglo', 'kmeans', 'gmm' or 'lda'.")

    def save_csv(self, filename, data):
        if os.path.exists(f"data/{self.project_id}/{filename}.csv"):
            data_saved = pd.read_csv(f"data/{self.project_id}/{filename}.csv")
            data = pd.concat([data, data_saved])
            data.to_csv(f"data/{self.project_id}/{filename}.csv", index=False)
        else:
            data.to_csv(f"data/{self.project_id}/{filename}.csv", index=False)
