import requests

s = requests.Session()

# Get login page and extract CSRF token
r = s.get('http://127.0.0.1:5000/login')
token = r.text.split('name="csrf_token" value="')[1].split('"')[0]

# Login
r = s.post('http://127.0.0.1:5000/login',
           data={'email': 'admin@smartvax.com', 'password': 'Admin@1234', 'csrf_token': token},
           allow_redirects=True)
print(f"LOGIN: {r.status_code} -> {r.url}")

pages = ['/', '/dashboard', '/schedule', '/history', '/recommendations',
         '/reminders', '/admin', '/chatbot', '/download_report']

for p in pages:
    try:
        r2 = s.get('http://127.0.0.1:5000' + p, allow_redirects=True)
        status = r2.status_code
        label = 'OK' if status == 200 else 'FAIL'
        has_err = 'Internal Server Error' in r2.text or 'jinja2' in r2.text.lower() or 'traceback' in r2.text.lower()
        if has_err:
            label = 'JINJA/SERVER ERROR'
            # Find the error message
            for keyword in ['jinja2.exceptions', 'TemplateError', 'UndefinedError', 'AttributeError']:
                idx = r2.text.lower().find(keyword.lower())
                if idx >= 0:
                    snippet = r2.text[max(0, idx-50):idx+300]
                    print(f"  {label} {status} {p}: {snippet[:200]}")
                    break
            else:
                print(f"  {label} {status} {p}")
        else:
            print(f"  {label} {status} {p}")
    except Exception as e:
        print(f"  EXCEPTION {p}: {e}")

# Test chatbot API
try:
    r3 = s.post('http://127.0.0.1:5000/api/chat',
                json={'message': 'What vaccines are recommended for children?'},
                headers={'X-CSRFToken': token, 'Content-Type': 'application/json'})
    data = r3.json()
    print(f"\nCHATBOT API: {r3.status_code}")
    print(f"  intent: {data.get('intent')}")
    print(f"  confidence: {data.get('confidence')}%")
    print(f"  response[:100]: {data.get('response', '')[:100]}")
except Exception as e:
    print(f"CHATBOT API ERROR: {e}")
