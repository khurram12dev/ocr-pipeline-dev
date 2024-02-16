# This is for a FastAPI app to test the api for ocr pipeline
import os
import base64
import io
import shutil
import json
from collections import OrderedDict
from pydantic import BaseModel

from fastapi import FastAPI, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import easyocr
from PyPDF2 import PdfFileReader

from utils import Utils, get_entity, convert_dict_generic, addendum_extract
from signature_detection import SignatureDetectionPipeline

pdf_dir = 'pdf_dir'
os.makedirs(pdf_dir, exist_ok=True)
annotations_dir = 'annotations'
ocr = easyocr.Reader(lang_list=['en'])
signature_detection = SignatureDetectionPipeline()

util = Utils(pdf_dir)
util.get_ocr(ocr)

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {'.pdf',}


def process():
    addendums = OrderedDict()
    image_json = {}
    master_json = {}
    pdfs = util.get_pdfs
    for pdf in pdfs:
        temp = util.get_forms(pdf)
        image_json.update(temp)
    
    for extracted_form in image_json:
    # extracted_form_name = extracted_form
        master_json[extracted_form] = {}
        for index, img in enumerate(image_json[extracted_form]):
            if extracted_form == 'TOA':
                if len(addendums) < 1:
                    addendums['page_0'] = {}
                    addendums['page_0'].update(get_entity(os.path.join(annotations_dir, f'{extracted_form}.json'), img, ocr))
                else:
                    temp_key = 'page_' + str(int(list(addendums.keys())[-1].split('_')[-1]) + 1)
                    addendums[temp_key]={}
                    addendums[temp_key].update(get_entity(os.path.join(annotations_dir, f'{extracted_form}.json'), img, ocr))
            else:
                temp = get_entity(os.path.join(annotations_dir, f'{extracted_form}_{index}.json'), img, ocr, signature_detection)
                master_json[extracted_form].update(temp)

    return master_json, addendums


class PDFRequest(BaseModel):
    encoded_pdf: str

def update_empty_values(addendum_data, main_data):
    
    for document, data in addendum_data.items():
        extra = []
        for question in data.keys():
            if question in main_data[document].keys():
                main_data[document][question] = data[question]
            else:
                extra.append(data[question])
        if extra:
            main_data[document]['extra_detail'] = extra
        
    return main_data

@app.post("/upload-pdf/")
async def get_pdf_file(file: dict):
    # print(pdf.)
    pdf_file = base64.b64decode(file['encoded_pdf'])
    # print(pdf_file)
    # Use shutil to save the uploaded file to a new location
    with open(os.path.join(pdf_dir, 'temp.pdf'), "wb") as file:
        file.write(pdf_file)
    
    # results contain the information for forms as keys and entities 
    # values, addendums contain the pages as keys and thier 
    # explanation as values
    result, addendums = process()
    
    with open('sample.json', 'w') as json_file:
        json.dump(result, json_file, indent=4)
    
    for form in result:
        result[form] = convert_dict_generic(result[form])
    
    if addendums:
        for form in addendums:
            addendums[form] = convert_dict_generic(addendums[form], sep='|')
        
        
        addendums = addendum_extract(addendums)
        
        result = update_empty_values(addendums, result)
    
    print('debug')
    return result
    
# run the uvicorn service
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, limit_max_requests=100000000)    
