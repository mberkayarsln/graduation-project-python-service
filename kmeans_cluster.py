from sklearn.cluster import KMeans


def cluster_points(df, k=5, random_state=42):
    coords = df[['lat', 'lon']].values
    kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
    df['cluster'] = kmeans.fit_predict(coords)
    return df, kmeans.cluster_centers_
