import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)
try:
    models = genai.list_models()
    print('Available models:')
    for m in models:
        print(m['name'], 'methods:', m.get('supported_methods', m.get('features', 'n/a')))
except Exception as e:
    print('error', type(e), e)
