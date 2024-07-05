from fastapi import FastAPI
from pydantic import BaseModel
from mangum import Mangum
import requests
import json
import asyncio
import aiohttp

app = FastAPI()
handler = Mangum(app)


class DataModel(BaseModel):
    data: str

class CapacityAuthentication(BaseModel):
    client_secret: str
    client_id: str

class CapacityShipmentConfirmation(BaseModel):
    token: str
    key: str
    batch_date: str
    max_batches: int

@app.get("/")
def index():
    return 'Hello Allyssa!!!!'


@app.post("/")
def processs_post(data: DataModel):
    return data

@app.post("/getToken")
def get_token(data: CapacityAuthentication):
    client_id = data.client_id
    client_secret = data.client_secret
    url ="https://api-integration.capacityllc.com/token"
    headers = {
        'Content-Type': 'application/json'
    }
    myjson = {
        'client_secret': client_secret,
        'client_id': client_id,
        'grant_type': 'client_credentials'
    }
    body = requests.post(url,data=myjson).json()
    if "access_token" in body:
        return {
            'access_token': body['access_token']
        }
    else:
        return {
            'access_token': ''
        }

@app.post("/getShipmentConfirmation")
async def get_shipment_confirmations(data: CapacityShipmentConfirmation):
    semaphore = asyncio.Semaphore(data.max_batches)
    tasks = [sub_get_confirmation_data(i, data, semaphore) for i in range(1, data.max_batches + 1)]
    results = await asyncio.gather(*tasks)
    finalArr = []
    for result in results:
        finalArr.extend(result['orders'])
    return {
        'batch_date': data.batch_date,
        'orders': finalArr
    }

async def sub_get_confirmation_data(batch_number, data: CapacityShipmentConfirmation, semaphore):
    async with semaphore:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {data.token}"
        }
        payload = json.dumps({
            "key": data.key,
            "batch_num": batch_number,
            "batch_date": data.batch_date
        })
        url = "https://api-integration.capacityllc.com/api/order/track"
        #print(payload)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload, ssl=False) as response:
                body = await response.json()
                if "orderlist" in body:
                    return {
                        "batch_number": batch_number,
                        "orders": [order['masterorderid'] for order in body['orderlist']]
                    }
                else:
                    return {
                        "batch_number": batch_number,
                        "orders": []
                    }