"""KMeans Clusterer - wrapper for scikit-learn KMeans."""
from sklearn.cluster import KMeans
import numpy as np


class KMeansClusterer:
    """KMeans clustering wrapper with convenience methods."""
    
    def __init__(self, n_clusters=5, random_state=42, n_init=10):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.n_init = n_init
        self.model = None
        self.cluster_centers_ = None
        self.labels_ = None
        self.inertia_ = None
    
    def fit(self, coordinates):
        """
        Fit KMeans model to coordinates.
        
        Args:
            coordinates: Array of shape (n_samples, 2) with [lat, lon]
        
        Returns:
            self
        """
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
        """
        Fit model using a DataFrame.
        
        Args:
            df: DataFrame with lat/lon columns
            lat_col: Name of latitude column
            lon_col: Name of longitude column
        
        Returns:
            Tuple of (df with cluster column, cluster centers)
        """
        coords = df[[lat_col, lon_col]].values
        self.fit(coords)
        
        df = df.copy()
        df['cluster'] = self.labels_
        
        return df, self.cluster_centers_
    
    def predict(self, coordinates):
        """Predict cluster for new coordinates."""
        if self.model is None:
            raise ValueError("Model has not been fit yet!")
        
        return self.model.predict(coordinates)
    
    def get_cluster_sizes(self):
        """Return dict of cluster_id -> count."""
        if self.labels_ is None:
            raise ValueError("Model has not been fit yet!")
        
        unique, counts = np.unique(self.labels_, return_counts=True)
        return dict(zip(unique, counts))
    
    def get_stats(self):
        """Return clustering statistics."""
        if self.labels_ is None:
            raise ValueError("Model has not been fit yet!")
        
        return {
            'n_clusters': self.n_clusters,
            'inertia': self.inertia_,
            'cluster_sizes': self.get_cluster_sizes()
        }
