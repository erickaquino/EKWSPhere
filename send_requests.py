import requests

url ="http://127.0.0.1:8000/getToken"
ship_confirm_url = "http://127.0.0.1:8000/getShipmentConfirmation"
myjson = {
    'client_secret': 'fqju**J@U)N^d}`q8tQ',
    'client_id': 'juststeven.capacity.client',
    'grant_type': 'client_credentials'
}

shipConfirmPayload = {
    "key": "CD343BFA-3109-44D6-A4CE-63313F98B8C1",
    "batch_date": "2024-07-01",
    "token": None,
    "max_batches": 2
}

token = requests.post(url,json=myjson).json()['access_token']
print(token)

if token != "":
    shipConfirmPayload['token'] = token
    print(shipConfirmPayload)
    ship_confirm_data = requests.post(ship_confirm_url,json=shipConfirmPayload).json()
    print(ship_confirm_data)

