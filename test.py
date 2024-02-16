from utils import Utils

utils = Utils('downloads')
utils.read_pdfs('output')

exit()

import easyocr

def read_text_from_image(image_path, language='en'):
    reader = easyocr.Reader([language])
    result = reader.readtext(image_path)
    return result

# Example usage
image_path = 'output/sample3.jpeg'
text_result = read_text_from_image(image_path)

# Display the result
for detection in text_result:
    text = detection[1]
    print(f"Detected text: {text}")
