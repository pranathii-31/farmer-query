import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('HUGGINGFACE_API_TOKEN')
models = [
    'nateraw/vit-base-beans',
    'microsoft/resnet-50',
    'linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification',
    'google/vit-base-patch16-224'
]

headers = {"Authorization": f"Bearer {token}"}

for model in models:
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    print(f"Testing model: {model}")
    # Using a dummy image (small 1x1 black pixel)
    dummy_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDAT\x08\xd7c\x60\x60\x60\x00\x00\x00\x04\x00\x01\x27\x34\x2e\x2f\x00\x00\x00\x00IEND\xaeB`\x82'
    try:
        response = requests.post(api_url, headers=headers, data=dummy_image)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)
