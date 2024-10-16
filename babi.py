import requests
import json

# Azure OpenAI endpoint and API key
endpoint = "https://resume-scanner.openai.azure.com/openai/deployments/gpt-35-turbo-16k/chat/completions?api-version=2024-08-01-preview"
api_key = "4960b7d3c80e4043a9849ea4a5add5d8"

# Request headers with your API key
headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}

# The data for the completion request
data = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a joke."}
    ],
    "max_tokens": 50
}

# Make the request
response = requests.post(endpoint, headers=headers, json=data)

# Output the response
if response.status_code == 200:
    completion = response.json()
    print(completion['choices'][0]['message']['content'])
else:
    print(f"Request failed with status code {response.status_code}: {response.text}")