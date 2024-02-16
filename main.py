import os
import json
import time


import easyocr
import cv2
import numpy as np

from scripts import *
from utils import Utils, get_entity


tic = time.time()
image_json = {}
master_json = {}
pdf_dir = 'pdf_dir'
annotations_dir = 'annotations'
ocr = easyocr.Reader(lang_list=['en'])
# read pdf files

util = Utils(pdf_dir)
pdfs = util.get_pdfs
# load the ocr
util.get_ocr(ocr)


# extract forms based images in a json file
for pdf in pdfs:
    temp = util.get_forms(pdf)
    image_json.update(temp)
print(time.time() - tic)
# print(image_json.keys())

# extract the data from the json file
tic = time.time()
for form in image_json:
    # form_name = form
    master_json[form] = {}
    for index, img in enumerate(image_json[form]):
        
        temp = get_entity(os.path.join(annotations_dir, f'{form}_{index}.json'), img, ocr)
        master_json[form].update(temp)


with open('master.json', 'w') as json_file:
        json.dump(master_json, json_file, indent=4)

print(time.time() - tic)
print(master_json.keys())
# recognize the document