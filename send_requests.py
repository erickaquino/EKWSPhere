import requests

url ="http://127.0.0.1:8000"
myjson = {'data': 'somevalue'}



print(requests.get(url).json())

print(requests.post(url,json=myjson).json())