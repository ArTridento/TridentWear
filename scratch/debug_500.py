import urllib.request

try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/products')
    print("Status:", response.getcode())
    print("Body:", response.read().decode())
except urllib.error.HTTPError as e:
    print("Status:", e.code)
    print("Body:", e.read().decode())
except Exception as e:
    print("Error:", str(e))
