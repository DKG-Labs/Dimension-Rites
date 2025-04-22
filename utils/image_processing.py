import cv2
import numpy as np
from PIL import Image, ImageChops
from pixelmatch.contrib.PIL import pixelmatch
import logging

def mask_image(image_path):
    img = cv2.imread(image_path, 1)
    if img is None:
        logging.warning(f"Image not found or failed to load: {image_path}")
        return None, None
    img = cv2.resize(img, (0, 0), None, 0.4, 0.4)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    canny = cv2.Canny(blur, 10, 70)
    _, mask = cv2.threshold(canny, 70, 255, cv2.THRESH_BINARY)
    return _, mask

# def mse(img1, img2):
#     h, w = img1.shape
#     diff = cv2.subtract(img1, img2)
#     err = np.sum(diff ** 2)
#     mse_value = err / (float(h * w))
#     return mse_value, diff

def mse_diff(img1, img2):
    diff = cv2.subtract(img1, img2)
    err = np.sum(diff.astype('float')**2)
    return err / (img1.size), diff

def image_chops_diff(img1_path, img2_path):
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)
    diff = ImageChops.difference(img1, img2)
    return diff, diff.size

def image_diff(img1_path, img2_path):
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)
    img_diff = Image.new('RGBA', img1.size)
    mismatch = pixelmatch(img1, img2, img_diff, includeAA=True)
    logging.info(f'Number of mismatched pixels: {mismatch}')
    return img_diff, mismatch

def find_largest_cluster(diff_image, resolution):
    _, binary_image = cv2.threshold(diff_image, 127, 255, cv2.THRESH_BINARY)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_image, connectivity=8)
    max_cluster_size = 0
    largest_cluster_distance = 0
    for label in range(1, num_labels):
        cluster_size = stats[label, cv2.CC_STAT_AREA]
        if cluster_size > max_cluster_size:
            cluster_coords = np.column_stack(np.where(labels == label))
            largest_cluster_distance = len(cluster_coords) * resolution
            max_cluster_size = cluster_size
    return largest_cluster_distance
