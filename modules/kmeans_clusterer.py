from sklearn.cluster import KMeans
import numpy as np


class KMeansClusterer:
    
    def __init__(self, n_clusters=5, random_state=42, n_init=10):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.n_init = n_init
        self.model = None
        self.cluster_centers_ = None
        self.labels_ = None
        self.inertia_ = None
    
    def fit(self, coordinates):
        self.model = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=self.n_init
        )
        
        self.labels_ = self.model.fit_predict(coordinates)
        self.cluster_centers_ = self.model.cluster_centers_
        self.inertia_ = self.model.inertia_
        
        return self
    
    def fit_dataframe(self, df, lat_col='lat', lon_col='lon'):
        coords = df[[lat_col, lon_col]].values
        self.fit(coords)
        
        df = df.copy()
        df['cluster'] = self.labels_
        
        return df, self.cluster_centers_
    
    def predict(self, coordinates):
        if self.model is None:
            raise ValueError("Model henüz fit edilmedi!")
        
        return self.model.predict(coordinates)
    
    def get_cluster_sizes(self):
        if self.labels_ is None:
            raise ValueError("Model henüz fit edilmedi!")
        
        unique, counts = np.unique(self.labels_, return_counts=True)
        return dict(zip(unique, counts))
    
    def get_stats(self):
        if self.labels_ is None:
            raise ValueError("Model henüz fit edilmedi!")
        
        return {
            'n_clusters': self.n_clusters,
            'inertia': self.inertia_,
            'cluster_sizes': self.get_cluster_sizes()
        }
