from django.http import JsonResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
import openai
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from .utils import outputgenerator
from pathlib import Path
import json

openai.api_key = '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'

MAX_SIZE = 20
page_range = 20
page_end_range = 20

elasticsearch_url = 'https://3df13a502759404ea768a4fc5b1c723d.ap-south-1.aws.elastic-cloud.com:80'
elasticsearch_username = 'elastic'
elasticsearch_password = 'TNLo1KLqA8PIk23CFVDoW7UJ'
index_name = 'legal_content'
# es = Elasticsearch([elasticsearch_url], basic_auth=(elasticsearch_username, elasticsearch_password))

es = Elasticsearch(
    cloud_id="nyay:YXAtc291dGgtMS5hd3MuZWxhc3RpYy1jbG91ZC5jb206NDQzJDNkZjEzYTUwMjc1OTQwNGVhNzY4YTRmYzViMWM3MjNkJDAxYjNmYmUxNTQ5MzQ5NmRhZWYyNzA4N2M1ODdmNGMx",  # Note the port number
    basic_auth=('elastic', 'TNLo1KLqA8PIk23CFVDoW7UJ')
)

@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_file(request):
    try: 
        file = request.FILES['file']
        id = (file.name + str(file.size)).replace("\n", "").replace("\r", "").replace(" ", "")
        print(f"Document Id: {id}")

        results = get_results(id)
        if results:
            return JsonResponse(results[0], safe=False)

        prompt_response = process_file_in_parallel(file, Path('/Users/adityapandey/Desktop/NyaayBackend/hello/myproject/resources/prompt_first.txt'))
        print("ChatGPT Response: ", prompt_response) 

        file_path="gpt.txt"
        with open(file_path, 'w') as file:
        # Write the text content to the file
              file.write(prompt_response)
        final_output = outputgenerator.generate(prompt_response, id)  # Implement the logic for generate_efiling_output function
        
        print("Final output: ",final_output)
        persist(id, final_output)


        print(f"Finished processing file: {file.name}")

        return JsonResponse(json.loads(final_output))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_file_extract_entity(request):
    try:
        file = request.FILES['file']
        id = (file.name + str(file.size)).replace("\n", "").replace("\r", "").replace(" ", "")
        print(f"Document Id: {id}")

        results = get_results(id)
        if results:
            return JsonResponse(results[0], safe=False)

        prompt_response = process_file_in_parallel(file,Path('/Users/adityapandey/Desktop/NyaayBackend/hello/myproject/resources/prompt_first.txt'))
        final_output = outputgenerator.generate(prompt_response, id)
        if es.ping():
            print("Connected to Elasticsearch on Elastic Cloud!")
        else:
            print("Failed to connect to Elasticsearch on Elastic Cloud!")

        persist(id, final_output)

        print(f"Finished processing file: {file.name}")

        return JsonResponse(json.loads(final_output))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def persist(id, content):
    # Define the document you want to index
    doc = {
        '_index': index_name,
        '_id': id,
        '_source': content
    }

    # Index the document
    if es.ping():
        print("Connected to Elasticsearch on Elastic Cloud!")
    else:
        print("Failed to connect to Elasticsearch on Elastic Cloud!")
    try: 
            # Check if the index does not already exist
        if not es.indices.exists(index=index_name):
            es.indices.create(index=index_name)
            print(f"Index {index_name} created successfully!")
        print("Content type: ",type(content))
        print("Content: ",content)
        print(f"Uploading to Idex: {index_name}")
        # resp = es.index(index=index_name, id=id, document={
        #     "id": id,
        #     "content": content
        # })
    except: 
        print("Error: Not able to upload on elastic cloud")

def execute_persist(request):
    # Set up the request for Elasticsearch
    request = request
    request['refresh'] = 'true'  # Set to 'true' for immediate refresh

    # Use the streaming_bulk method to perform the indexing
    successes = 0
    # for success, info in streaming_bulk(client=es, actions=[request]):
    #     if success:
    #         successes += 1

    print(f"Successfully indexed {successes} documents")

def get_results(id):
    results = []
    
    # Define the search query
    search_query = {
        "query": {
            "match": {
                "_id": id
            }
        },
        "size": MAX_SIZE  # Set the maximum number of results to return
    }

    try:
        search_response = es.search(index=index_name, body=search_query)
        hits = search_response['hits']['hits']
        
        for hit in hits:
            results.append(hit['_source'])
    except:
        print("No data found on elastic cloud")

    return results

def generate_efiling_output(input_list, id):
    # Implement the logic to generate the final output here
    pass

def process_file_in_parallel(file, prompt_name):
    end_page = 0
    document = None
    try:
        document = PdfReader(file)
        end_page = len(document.pages)
        print(f"Document: {file.name} has {end_page} pages")
    except Exception as e:
        print(f"Error loading PDF document: {e}")

    prompt_response = []
    total_tasks = 0

    for i in range(1, end_page + 1):
        if i > page_range and i <= end_page - page_end_range:
            continue

        print("=============== i: ", i)

        print(f"Processing page: {i}")
        text = get_text_from_document(document, i)
        if not text:
            print(f"No text identified at page number: {i}")
            continue

        total_tasks += 1
        prompt = read_text_from_file(prompt_name)
        # print("OCR Text: ", text)
        # print("Prompt:<----> ", prompt)
        gpt_resp = complete_prompt(prompt + "\n" + text)
        print("Type gpt resp: ", type(gpt_resp))
        print("Response GPT: ",gpt_resp)
        gpt_resp=str(gpt_resp)
        prompt_response.append(gpt_resp)
    print(prompt_response[0])

    return prompt_response

def complete_prompt(prompt):
    resp =  openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=100
    ).choices[0].text
    # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ Prompt: ",prompt)
    print("************************** Ans: ",resp)
    return resp

def get_text_from_document(document, page_number):
    try:
        page = document.pages[page_number - 1]  # Use reader.pages[page_number] instead of getPage()
        text = page.extract_text()
        if not text or len(text) < 50:
            print(f"Empty content, trying OCR for page: {page_number}")
            ocr_text = ocr_pdf_text(document, page_number)
            if len(ocr_text) - len(text) > 20:
                text = ocr_text
                print(f"Using OCR for page: {page_number}")
        return text
    except Exception as e:
        print(f"Error extracting text from page {page_number}: {e}")
        return ""


def ocr_pdf_text(document, page_number):
    try:
        image = pdf_page_to_image(document, page_number)
        ocr_text = pytesseract.image_to_string(image)
        return ocr_text
    except Exception as e:
        print(f"Error performing OCR for page {page_number}: {e}")
        return ""

def pdf_page_to_image(document, page_number):
    page = document.getPage(page_number - 1)
    xObject = page['/Resources']['/XObject'].get_object()
    image = None

    for obj in xObject:
        if xObject[obj]['/Subtype'] == '/Image':
            image = xObject[obj]
            break

    if image:
        image_data = image.get_data()
        image_type = image['/Filter'][1:]
        image_file = InMemoryUploadedFile(image_data, None, "page.jpg", "image/jpeg", image_data.__sizeof__(), None)
        return image_file
    return None

def read_text_from_file(file_name):
    with open(file_name, "r") as file:
        return file.read()
    

# Define constants like page_range, page_end_range, etc.
page_range = 20
page_end_range = 20

