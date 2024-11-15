import cv2
import numpy as np
from PIL import Image, ImageChops
from pixelmatch.contrib.PIL import pixelmatch

def mask_image(filename1):
    img1 = cv2.imread(filename1, 1)
    if img1 is None:
        print("Image not found or failed to load")
    else:
        img1 = cv2.resize(img1, (0, 0), None, 0.4, 0.4)
       
    gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    canny = cv2.Canny(blur, 10, 70)
    ret, mask = cv2.threshold(canny, 70, 255, cv2.THRESH_BINARY)
    # plt.subplot(screenId), plt.imshow(mask, 'gray'), plt.title(filename1 + "_E"), plt.axis('off')
    return ret, mask
 
def mse(img1, img2):
   h, w = img1.shape
   diff = cv2.subtract(img1, img2)
   err = np.sum(diff**2)
   mse_value = err / (float(h * w))
   return mse_value, diff
 
def imageChops(filename1, filename2):
    img1 = Image.open(filename1)
    img2 = Image.open(filename2)
    diff = ImageChops.difference(img1, img2)
    return diff, diff.size
 
def imageDiff(filename1, filename2):
    img11 = Image.open(filename1)
    img21 = Image.open(filename2)
    img_diff = Image.new('RGBA', img11.size)
    mismatch = pixelmatch(img11, img21, img_diff, includeAA=True)
    print(f'Number of mismatched pixels: {mismatch}')
    return img_diff, mismatch