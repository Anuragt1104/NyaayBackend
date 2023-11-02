from django.http import JsonResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from django.core.files.uploadedfile import InMemoryUploadedFile
import pytesseract
from PyPDF2 import PdfFileReader
import openai
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from util.outputgenerator import generate, generate_efiling_output

openai.api_key = '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'

# Define your Elasticsearch server settings
elasticsearch_host = 'localhost'  # Replace with your Elasticsearch server host
elasticsearch_port = 9200  # Replace with your Elasticsearch server port
index_name = 'legal_content'  # Replace with your Elasticsearch index name

# Define constants like page_range, page_end_range, etc.
MAX_SIZE = 20
page_range = 20
page_end_range = 20

# Establish a connection to Elasticsearch
# es = Elasticsearch([{'host': elasticsearch_host, 'port': elasticsearch_port}])
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

        prompt_response = process_file_in_parallel(file, 'prompt_efiling.txt')
        final_output = generate_efiling_output(prompt_response, id)

        persist(id, final_output)

        print(f"Finished processing file: {file.name}")

        return JsonResponse(final_output)
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

        prompt_response = process_file_in_parallel(file, 'prompt_first.txt')
        final_output = generate(prompt_response, id)

        persist(id, final_output)

        print(f"Finished processing file: {file.name}")

        return JsonResponse(final_output)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['POST'])
@parser_classes([MultiPartParser])
def update_document(request):
    try:
        id = request.GET.get('id')
        content = request.body.decode('utf-8')

        # Create an UpdateRequest with the index, document ID, and updated content
        update_request = {
            "doc": {
                "content": content
            }
        }

        # Perform the update operation
        es.update(index=index_name, id=id, body=update_request)

        response_message = f"Value with ID {id} updated successfully."
        return JsonResponse(response_message, safe=False)

    except Exception as e:
        error_message = f"Error occurred: {str(e)}"
        return JsonResponse({"error": error_message}, status=500)
def persist(id, content):
    # Define the document you want to index
    doc = {
        '_index': index_name,
        '_id': id,
        '_source': content
    }

    if es.ping():
        print("Connected to Elasticsearch on Elastic Cloud!")
    else:
        print("Failed to connect to Elasticsearch on Elastic Cloud!")

    # Index the document
    try: 
            # Check if the index does not already exist
        if not es.indices.exists(index=index_name):
            es.indices.create(index=index_name)
            print(f"Index {index_name} created successfully!")
        resp = es.index(index=doc['_index'], id=doc['_id'], document=doc)
    except: 
        print("Error: Not able to upload on elastic cloud")

    # Index the document
   
    
def execute_persist(request):
    # Set up the request for Elasticsearch
    request = request
    request['refresh'] = 'true'  # Set to 'true' for immediate refresh

    # Use the streaming_bulk method to perform the indexing
    successes = 0
    for success, info in streaming_bulk(client=es, actions=[request]):
        if success:
            successes += 1

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
    except Exception as e:
        print(f"An error occurred: {e}")

    return results



def process_file_in_parallel(file, prompt_name):
    end_page = 0
    document = None
    try:
        document = PdfFileReader(file)
        end_page = document.getNumPages()
        print(f"Document: {file.name} has {end_page} pages")
    except Exception as e:
        print(f"Error loading PDF document: {e}")

    prompt_response = []
    total_tasks = 0

    for i in range(1, end_page + 1):
        print("<-------------> ",i)
        if i > page_range and i <= end_page - page_end_range:
            continue

        print(f"Processing page: {i}")
        text = get_text_from_document(document, i)
        if not text:
            print(f"No text identified at page number: {i}")
            continue



        total_tasks += 1
        prompt = read_text_from_file(prompt_name)
        print("OCR Text: ", text)
        prompt_response.append(complete_prompt(prompt + "\n" + text))

    return prompt_response

def complete_prompt(prompt):
    return openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=100
    ).choices[0].text

def get_text_from_document(document, page_number):
    try:
        page = document.getPage(page_number - 1)  # Python uses 0-based indexing for pages
        text = page.extractText()
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
