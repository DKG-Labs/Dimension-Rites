import cv2
import numpy as np

def find_largest_cluster(diff_image, resolution):
    """
    Identify the largest significant cluster of white dots and quantify its distance in millimeters.
    
    :param diff_image: Binary image where white dots represent differences.
    :param size_threshold: Minimum size of clusters to be considered significant.
    :param resolution: Resolution in mm per pixel.
    :return: Total distance of the largest cluster in millimeters.
    """
    _, binary_image = cv2.threshold(diff_image, 127, 255, cv2.THRESH_BINARY)
    
    # Find connected components (clusters)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_image, connectivity=8)
    
    max_cluster_size = 0
    largest_cluster_distance = 0

    for label in range(1, num_labels):  # Label 0 is the background
        cluster_size = stats[label, cv2.CC_STAT_AREA]
        if cluster_size > max_cluster_size:  # Update largest cluster
            cluster_coords = np.column_stack(np.where(labels == label))
            largest_cluster_distance = len(cluster_coords) * resolution
            max_cluster_size = cluster_size

    return largest_cluster_distance