import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def complete(request):
    try:
        api_key = "your_openai_api_key"  # You can replace this with your OpenAI API key
        api_url = "https://api.openai.com/v1/completions"
        request_data = json.loads(request.body.decode('utf-8'))
        prompt = request_data["prompt"]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        data = {
            "prompt": prompt,
            "model": "text-davinci-003",
            "temperature": 0,
            "max_tokens": 2000
        }

        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            response_data = response.json()
            choices = response_data["choices"]
            if choices:
                choice = choices[0]
                text = choice["text"]
                if "JSON Output:" in text:
                    text = text.replace("JSON Output:", "")
                if "~~~~" in text:
                    text = text.split("~~~~", 1)[1]
                return JsonResponse({"result": text})
            else:
                return JsonResponse({"error": "No completion text in response"})
        else:
            return JsonResponse({"error": f"Request failed with status: {response.status_code}"}, status=response.status_code)

    except Exception as e:
        return JsonResponse({"error": f"Request failed: {str(e)}"}, status=500)

@csrf_exempt
@require_POST
def complete_translation(request):
    try:
        api_key = "your_openai_api_key"  # You can replace this with your OpenAI API key
        api_url = "https://api.openai.com/v1/completions"
        request_data = json.loads(request.body.decode('utf-8'))
        prompt = request_data["prompt"]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        data = {
            "prompt": prompt,
            "model": "text-davinci-003",
            "temperature": 0,
            "max_tokens": 2000
        }

        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            response_data = response.json()
            choices = response_data["choices"]
            if choices:
                choice = choices[0]
                text = choice["text"]
                return JsonResponse({"result": text})
            else:
                return JsonResponse({"error": "No completion text in response"})
        else:
            return JsonResponse({"error": f"Request failed with status: {response.status_code}"}, status=response.status_code)

    except Exception as e:
        return JsonResponse({"error": f"Request failed: {str(e)}"}, status=500)
