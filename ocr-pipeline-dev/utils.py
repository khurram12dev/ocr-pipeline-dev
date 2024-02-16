from collections import OrderedDict
import json
import os
import re

from pdf2image import convert_from_path
import cv2
import numpy as np

from addendum_utils import combine_explanations, remove_empty_strings, organize_documents, organize_records, is_single_cap_letter, clean_line
from signature_detection import SignatureDetectionPipeline


class Utils:
    
    """This class defines the utilities for the ocr pipeline
    """

    def __init__(self, pdf_dir) -> None:
        self.pdf_dir = pdf_dir
        self.images = OrderedDict()
        self.master_json = None
        self.ocr = None
        self.done_dir = 'done_dir'
        with open('data/documents.json', 'r') as file:
            self.doc = json.load(file)

    @property
    def get_pdfs(self) -> list:
        """Read pdf files from a directory and same images in a temporary directory
        """
        return [os.path.join(self.pdf_dir, file) for file in os.listdir(self.pdf_dir)]


    def remove_special_characters(self, input_string):

        pattern = r'[^a-zA-Z0-9\s]'
        result = re.sub(pattern, '', input_string)
        
        return result


    def store_text(self, collection):
        return [text for (bbox, text, prob) in collection]


    def clear_directories(self):
        """Clears all the temporary directories
        """
        pass


    def get_ocr(self, ocr):
        self.ocr = ocr
    

    def get_forms(self, pdf_path):
        """
        Takes input a single pdf file
        Save text from the images in a json file based on the form name detected
        This can be used to sort the documents
        """
        
        images = convert_from_path(pdf_path, dpi=400,poppler_path=r"C:\Program Files\poppler-23.08.0\Library\bin")
        os.remove(pdf_path)
        CURRENT_KEY= ''
        KEY_ADDED = False
        pages = {}

        for i, img in enumerate(images):
            print('checking image: ',i)
            img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
            results = self.ocr.readtext(img[:int(img.shape[0] * 0.15),:,:])
            trimmed = results[:50]
            for index, (bbox, text, prob) in enumerate(trimmed):
                if 'form ' in text.lower():
                    if 'perform' in text.lower():
                        continue
                    try:
                        temp = text.lower().split('form ')[1].split(' ')[0]
                        temp = self.remove_special_characters(temp).upper()
                        if temp == 'TOA' and temp in pages.keys():
                            # print(len(pages[temp]))
                            pages[temp].append(img)
                            break
                        elif temp == 'TOA' and temp not in pages.keys():
                            pages[temp] = [img]
                            break
                    except:
                        continue
                    for key in self.doc:
                        if temp == key and self.doc[key] == None and key not in pages:
                            pages[key] = [img]
                            CURRENT_KEY  = key
                            KEY_ADDED = True
                            break
                    if KEY_ADDED:
                        KEY_ADDED = False
                        break

                if index == len(trimmed) - 1:
                    pages[CURRENT_KEY].append(img)
        
        return pages
        # with open(f'temp_jsons/{pdf_name}.json', 'w') as json_file:
        #     json.dump(pages, json_file, indent=4)

def crop_center(img, crop_percentage=0.6):
    # Get the dimensions of the image
    height, width = img.shape[:2]

    # Calculate the crop size as crop_percentage% of the original image size
    crop_width = int(width * crop_percentage)
    crop_height = int(height * crop_percentage)

    # Calculate the center of the image
    center_x, center_y = width // 2, height // 2

    # Calculate the coordinates of the top left corner of the cropping rectangle
    top_left_x = center_x - crop_width // 2
    top_left_y = center_y - crop_height // 2

    # Crop the image
    cropped_img = img[top_left_y:top_left_y + crop_height, top_left_x:top_left_x + crop_width]

    return cropped_img


def detect_check(image):
    """
    Check if a checkbox is checked or not.

    Parameters:
    image (ndarray): input image.

    Returns:
    bool: True if blue color is found, False otherwise.
    """
    try:
        image = crop_center(image, 0.8)
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([110, 50, 50])
        upper_blue = np.array([130, 255, 255])
        mask = cv2.inRange(hsv_image, lower_blue, upper_blue)
    
        return np.any(mask)
    
    except Exception as e:

        print(f"An error occurred: {e}")

        return False

def get_entity(json_path, img, ocr, signature_detector=None):
    
    """get required entities from the image

    Parameters:
    json_path (str): path to the json file.
    img (ndarray): input image.
    ocr : ocr object for detection.
    
    Returns:
        dict: returns a dictionary of extracted entities.
    """

    info = {}
    # print(json_path)
    with open(json_path) as file:
        data = json.load(file)

    id = list(data['_via_img_metadata'].keys())[0]
    
    for region in data['_via_img_metadata'][id]['regions']:
        coor = region['shape_attributes']
        entity = region['region_attributes'][list(region['region_attributes'].keys())[0]]
        x_min = coor['x']
        y_min = coor['y']
        x_max = x_min + coor['width']
        y_max = y_min + coor['height']
        
        if region['region_attributes']['tag'] == 'checkbox':
            out = detect_check(img[y_min:y_max, x_min:x_max, : ])
            if out :
                out = "True"
            else:
                out = "False"
        elif region['region_attributes']['tag'] == 'signature':
            # out = 'signature block' 
            out = signature_detector.run(img[y_min:y_max, x_min:x_max, : ])
            # print(out)
            # print(region['region_attributes']['Radio'])
            # out = signature_detector.run()
            if out == 'Handwritten':
                out = "True"
            else:
                out = "False"
        else: 
            out = ocr.readtext(img[y_min:y_max, x_min:x_max, : ])
            out = ' '.join([result[1] for result in out])

        info[entity] = out

    return info

def convert_dict_generic(data, sep=' '):
    new_data = {}
    grouped_keys = {}

    # Group keys by their base name
    for key in data:
        key_parts = key.rsplit('_', 1)
        if len(key_parts) == 2 and key_parts[1].isdigit():
            base_key = key_parts[0]
            grouped_keys.setdefault(base_key, []).append(key)
        elif len(key_parts) == 2 and key_parts[1] in ['yes', 'no']:
            base_key = key_parts[0]
            if data[key] == "True":
                print("tt_TRUE",key)
                new_data[base_key] = key_parts[1]
        else:
            # Keep regular keys as they are
            new_data[key] = data[key]

    # Process versioned string keys
    for base_key, keys in grouped_keys.items():
        sorted_keys = sorted(keys, key=lambda x: int(x.rsplit('_', 1)[-1]))
        new_data[base_key] = sep.join(data[k] for k in sorted_keys)

    return new_data

# addendum extraction - onward

def clean_string(input_string):
    # Replace special characters with spaces
    cleaned_string = re.sub(r'[^\w\s]', ' ', input_string)
    
    # Replace multiple spaces with a single space
    cleaned_string = re.sub(r'\s+', ' ', cleaned_string).strip()
    
    return cleaned_string


def addendum_extract(data:dict)->dict:
    info = {}
    # combine the pages of addedum
    data = combine_explanations(data)
    data = data['explanation'].split('|')
    data = remove_empty_strings(data)
    data = organize_documents(data) #documents extracted
    data = organize_records(data)
    for form, questions in data.items():
        questions:dict
        info[form] = {}
        for question, explanation in questions.items():
            previous_key = None
            for statement in explanation:
                temp = clean_string(statement).split(' ')
                print(temp)
                if len(temp) > 1:
                    if is_single_cap_letter(temp[1]):
                        previous_key = f'{temp[0]}_{temp[1]}_explanation'
                        if previous_key in info[form].keys():
                            continue
                        info[form][previous_key] = ''
                    else:
                        info[form][previous_key] = info[form][previous_key]  + statement + '|'
                else:
                    info[form][previous_key] = info[form][previous_key] + statement+ '|'
    
    return info
                    
            
    print(data)
    # for document, questions in data.items():
    #     info[document] = {}
    #     for question in questions:
    #         pass

def organize_explanation(questions):
    """get exact explanations and location of the information from 
    addendums

    Args:
        question (dict): questions from organize records 
        
    Returns:
        dict: question numbers with thier text as values

    """
    for statement in questions:
        statement = clean_line(statement)

