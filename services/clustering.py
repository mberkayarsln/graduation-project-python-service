"""Clustering Service - handles employee clustering operations."""
import numpy as np
from core.cluster import Cluster
from utils.kmeans import KMeansClusterer


class ClusteringService:
    """Service for clustering employees into groups."""
    
    def __init__(self, config):
        self.config = config
        self.algorithm = 'kmeans'
        self.clusterer = None
    
    def cluster_employees(self, employees, num_clusters, random_state=None):
        """
        Cluster employees into groups.
        
        Args:
            employees: List of Employee objects
            num_clusters: Number of clusters to create
            random_state: Random seed for reproducibility
        
        Returns:
            List of Cluster objects with employees assigned
        """
        if self.algorithm == 'kmeans':
            return self._cluster_kmeans(employees, num_clusters, random_state)
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
    
    def _cluster_kmeans(self, employees, num_clusters, random_state):
        """Perform KMeans clustering."""
        self.clusterer = KMeansClusterer(
            n_clusters=num_clusters,
            random_state=random_state
        )
        coordinates = np.array([[emp.lat, emp.lon] for emp in employees])
        
        self.clusterer.fit(coordinates)
        
        # Create cluster objects
        clusters = []
        for i in range(num_clusters):
            center = tuple(self.clusterer.cluster_centers_[i])
            cluster = Cluster(id=i, center=center)
            clusters.append(cluster)
        
        # Assign employees to clusters
        for employee, cluster_id in zip(employees, self.clusterer.labels_):
            clusters[cluster_id].add_employee(employee)
        
        return clusters
    
    def find_optimal_clusters(self, employees, max_clusters=15):
        """Find optimal number of clusters using elbow method."""
        coordinates = np.array([[emp.lat, emp.lon] for emp in employees])
        
        inertias = []
        for k in range(1, min(max_clusters + 1, len(employees))):
            clusterer = KMeansClusterer(n_clusters=k, random_state=42)
            clusterer.fit(coordinates)
            inertias.append(clusterer.inertia_)
        
        # TODO: Implement elbow detection
        return self.config.NUM_CLUSTERS
    
    def get_clustering_stats(self):
        """Return clustering statistics."""
        if self.clusterer is None:
            return None
        
        return self.clusterer.get_stats()
