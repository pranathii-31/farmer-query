from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

# Try to find .env in the right place
env_path = '/Users/pranathi/Documents/farmer-query/online-module/farmer_query_engine/backend/.env'
load_dotenv(env_path)

token = os.getenv('HUGGINGFACE_API_TOKEN')
client = InferenceClient(model="nateraw/vit-base-beans", token=token)

print(f"Token found: {token is not None}")
# InferenceClient doesn't expose the URL easily, but we can try to call it
try:
    # Using a slightly more realistic dummy PNG (red 1x1)
    dummy_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff? \x00\x05\xfe\x02\xfe\xdcD\x05\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
    result = client.image_classification(dummy_image)
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
