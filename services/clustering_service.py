"""Clustering Service"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import numpy as np
from models.cluster import Cluster
from modules.kmeans_clusterer import KMeansClusterer


class ClusteringService:
    def __init__(self, config):
        self.config = config
        self.algorithm = 'kmeans'
        self.clusterer = None
    
    def cluster_employees(self, employees, num_clusters, random_state=None):
        if self.algorithm == 'kmeans':
            return self._cluster_kmeans(employees, num_clusters, random_state)
        else:
            raise ValueError(f"Desteklenmeyen algoritma: {self.algorithm}")
    
    def _cluster_kmeans(self, employees, num_clusters, random_state):
        self.clusterer = KMeansClusterer(
            n_clusters=num_clusters,
            random_state=random_state
        )
        coordinates = np.array([[emp.lat, emp.lon] for emp in employees])
        
        self.clusterer.fit(coordinates)
        
        clusters = []
        for i in range(num_clusters):
            center = tuple(self.clusterer.cluster_centers_[i])
            cluster = Cluster(id=i, center=center)
            clusters.append(cluster)
        
        for employee, cluster_id in zip(employees, self.clusterer.labels_):
            clusters[cluster_id].add_employee(employee)
        
        return clusters
    
    def find_optimal_clusters(self, employees, max_clusters=15):
        coordinates = np.array([[emp.lat, emp.lon] for emp in employees])
        
        inertias = []
        for k in range(1, min(max_clusters + 1, len(employees))):
            clusterer = KMeansClusterer(n_clusters=k, random_state=42)
            clusterer.fit(coordinates)
            inertias.append(clusterer.inertia_)
        
        return self.config.NUM_CLUSTERS
    
    def get_clustering_stats(self):
        if self.clusterer is None:
            return None
        
        return self.clusterer.get_stats()
