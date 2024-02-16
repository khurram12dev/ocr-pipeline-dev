import re


def combine_explanations(data:dict)->dict:
    """combines the explanation part of the addendum document 

    Args:
        data (dict): _description_

    Returns:
        _type_: _description_
    """
    if len(data.keys()) < 2:
        return data
    else:
        temp = data['page_0']
        for key in list(data.keys())[1:]:
            temp['explanation'] = temp['explanation'] + '|' + data[key]['explanation']
        return temp 

def remove_empty_strings(my_list)->list: 
    return [string for string in my_list if string]

def clean_line(text)->str:
    # Replace any character that is not a letter, a number, or a space with a space
    return re.sub(r"[^\w\s]", " ", text)

def organize_documents(list)->dict:
    documents = {}
    current_key = ''
    for line in list:
        if '[' in line:
            start = line.find('[')
            last = line.find(']')
            if last >= 0:
                current_key = line[start+1:last]
                if current_key not in documents.keys():
                    documents[current_key] = []
        else:
            documents[current_key].append(line)
    
    return documents 

def is_single_cap_letter(entry)->bool:
    return len(entry) == 1 and entry.isupper()

def organize_records(documents:dict)->dict:
    """organizes the questions from the document

    Args:
        documents (dict): this is the individual document that is 
        derieved from organize documents 

    Returns:
        dict: question numbers with thier text as values
    """
    nested_dict = {}
    # print(documents)

    for doc_key, contents in documents.items():
        nested_dict[doc_key] = {}
        current_question = None

        for index, line in enumerate(contents):
            if '(continued' in line.lower():
                continue
            # Find a pattern that matches "number)"
            print(line)
            match = re.match(r'(\d+\))', line)
            print(type(match))
            if match:
                current_question = match.group(1)
                print(current_question)
                # The number followed by ")"
                if current_question not in nested_dict[doc_key].keys():
                    nested_dict[doc_key][current_question] = []
                # if current_question in nested_dict[doc_key].keys():
                #     nested_dict[doc_key][current_question].append(line)
            elif current_question is not None:
                nested_dict[doc_key][current_question].append(line)

    return nested_dict
