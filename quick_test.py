import google.generativeai as genai

genai.configure(api_key='AIzaSyCO9FsiUHdVbVG5cXbRr_rDWhMkMVb9IYo')
try:
    m = genai.GenerativeModel(model_name='gemini-2.0-flash')
    r = m.generate_content('Hello')
    print('response', r.text)
except Exception as e:
    print('error', type(e), e)
