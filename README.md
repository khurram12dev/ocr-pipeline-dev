# ocr-pipeline

recommended python version is 3.9

install requirements uisng following command
~~~
pip install -r requirements.txt
~~~

for FastAPI demo, run the following command

~~~
python app.py
~~~

This will create a uvicorn server based fastapi where any pdf can be tested on the following link:
http://127.0.0.1:8000/docs

This api is currently recieving a base64 encoded pdf on a json key named 'encoded-pdf'.


Note: not all pdfs are added yet. you can only test SPQ for now.