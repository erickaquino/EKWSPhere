from fastapi import FastAPI
from pydantic import BaseModel
from mangum import Mangum
import requests
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta


app = FastAPI()
handler = Mangum(app)

class CapacityAuthentication(BaseModel):
    client_secret: str
    client_id: str


class CapacityShipmentConfirmation(BaseModel):
    token: str
    key: str
    start_date: str
    end_date: str
    max_batches: int

class CapacityShipmentConfirmationBasic(BaseModel):
    token: str
    key: str
    date: str
    batch: int
    is_full_list: bool


class CapacitySpecififOrderShipConfirm(BaseModel):
    key: str
    batch_date: str
    batch_number: int
    token: str
    order_number: str


class CeligoAuthentication(BaseModel):
    token: str
    url: str


class CeligoExport(BaseModel):
    params: CeligoAuthentication
    export_id: str


class CeligoFlow(BaseModel):
    params: CeligoAuthentication
    flow_id: str


class CeligoJob(BaseModel):
    params: CeligoAuthentication
    job_id: str


@app.get("/")
def index():
    return 'Ekwani API'


@app.post("/getToken")
def get_token(data: CapacityAuthentication):
    client_id = data.client_id
    client_secret = data.client_secret
    url = "https://api-integration.capacityllc.com/token"
    headers = {
        'Content-Type': 'application/json'
    }
    myjson = {
        'client_secret': client_secret,
        'client_id': client_id,
        'grant_type': 'client_credentials'
    }
    body = requests.post(url, data=myjson).json()
    if "access_token" in body:
        return {
            'access_token': body['access_token']
        }
    else:
        return {
            'access_token': ''
        }


@app.post("/getOrders")
async def get_orders(data: CapacityShipmentConfirmation):
    dates = get_date_range(data.start_date, data.end_date)
    semaphore = asyncio.Semaphore(data.max_batches)
    tasks = []
    for date in dates:
        for i in range(1, data.max_batches + 1):
            tasks.append(sub_get_confirmation_data(i, date, data, False, semaphore))
    results = await asyncio.gather(*tasks)
    finalArr = [result for result in results if len(result['orders']) > 0]
    return {
        'start_date': data.start_date,
        'end_date': data.end_date,
        'orders': finalArr
    }


@app.post("/getOrders/full")
async def get_orders_full(data: CapacityShipmentConfirmation):
    dates = get_date_range(data.start_date, data.end_date)
    semaphore = asyncio.Semaphore(data.max_batches)
    tasks = []
    for date in dates:
        for i in range(1, data.max_batches + 1):
            tasks.append(sub_get_confirmation_data(i, date, data, True, semaphore))
    results = await asyncio.gather(*tasks)
    finalArr = [result for result in results if len(result['orders']) > 0]
    return {
        'start_date': data.start_date,
        'end_date': data.end_date,
        'orders': finalArr
    }


async def sub_get_confirmation_data(batch_number, batch_date, data: CapacityShipmentConfirmation, is_full_list,
                                    semaphore):
    async with semaphore:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {data.token}"
        }
        payload = json.dumps({
            "key": data.key,
            "batch_num": batch_number,
            "batch_date": batch_date
        })
        url = "https://api-integration.capacityllc.com/api/order/track"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload, ssl=False) as response:
                body = await response.json()
                orders = []
                short_shipped_orders = {}
                is_short_shipped_orders_empty = False
                if is_full_list:
                    orders = body.get('orderlist', [])
                else:
                    full_orders = body.get('orderlist', [])
                    orders = set()

                    for order in full_orders:
                        masterorderid = order['masterorderid'].replace('Sales Order #', '')
                        orders.add(masterorderid)
                        if order['capacityShippedQuantity'] == 0:
                            if masterorderid not in short_shipped_orders:
                                short_shipped_orders[masterorderid] = []
                            short_shipped_orders[masterorderid].append(order['capacityProductID'])
                    orders = list(orders)
                    is_short_shipped_orders_empty = not bool(short_shipped_orders)
                if is_short_shipped_orders_empty:
                    return {
                        "batch_date": batch_date,
                        "batch_number": batch_number,
                        "orders": orders
                    }
                else:
                    return {
                        "batch_date": batch_date,
                        "batch_number": batch_number,
                        "orders": orders,
                        "short_shipped_orders": short_shipped_orders
                    }


@app.post("/getOrders/nonthread")
async def get_confirmation_data_non_threaded(data: CapacityShipmentConfirmationBasic):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {data.token}"
    }
    payload = json.dumps({
        "key": data.key,
        "batch_num": data.batch,
        "batch_date": data.date
    })
    print(payload)
    url = "https://api-integration.capacityllc.com/api/order/track"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload, ssl=False) as response:
            body = await response.json()
            orders = []
            short_shipped_orders = {}
            is_short_shipped_orders_empty = False
            if data.is_full_list:
                orders = body.get('orderlist', [])
            else:
                full_orders = body.get('orderlist', [])
                orders = set()

                for order in full_orders:
                    masterorderid = order['masterorderid'].replace('Sales Order #', '')
                    orders.add(masterorderid)
                    if order['capacityShippedQuantity'] == 0:
                        if masterorderid not in short_shipped_orders:
                            short_shipped_orders[masterorderid] = []
                        short_shipped_orders[masterorderid].append(order['capacityProductID'])
                orders = list(orders)
                is_short_shipped_orders_empty = not bool(short_shipped_orders)
            if is_short_shipped_orders_empty:
                return {
                    "batch_date": data.date,
                    "batch_number": data.batch,
                    "orders": orders
                }
            else:
                return {
                    "batch_date": data.date,
                    "batch_number": data.batch,
                    "orders": orders,
                    "short_shipped_orders": short_shipped_orders
                }

@app.post("/getShipmentConfirmation/specific")
async def get_specific_ship_confirm(data: CapacitySpecififOrderShipConfirm):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {data.token}"
    }
    payload = {
        "key": data.key,
        "batch_num": data.batch_number,
        "batch_date": data.batch_date
    }
    url = "https://api-integration.capacityllc.com/api/order/track"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload, ssl=False) as response:
            body = await response.json()
            print(body)
            orders = [x for x in body.get('orderlist', []) if x.get('masterorderid') == data.order_number]
            return {
                "order_number": data.order_number,
                "data": orders
            }


def get_date_range(start_date, end_date):
    # Convert input strings to date objects
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # Create a list to hold the date strings
    date_list = []

    # Iterate over the date range
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    return date_list


@app.post("/testCeligoConnection")
async def test_celigo_connection(data: CeligoAuthentication):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {data.token}"
    }
    url = data.url

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url}/connections", headers=headers, ssl=False) as response:
            return {
                "data": "success" if response.status == 200 else "false"
            }


@app.post("/runCeligoExport")
async def run_celigo_export(data: CeligoExport):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {data.params.token}"
    }
    url = data.params.url

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{url}/exports/{data.export_id}/invoke", headers=headers, ssl=False) as response:
            response_text = await response.text()
            try:
                # Attempt to parse the response as JSON
                body = json.loads(response_text)
            except json.JSONDecodeError as e:

                # Attempt to handle multiple JSON objects or non-JSON data
                json_objects = []
                start = 0
                while start < len(response_text):
                    try:
                        obj, index = json.JSONDecoder().raw_decode(response_text, start)
                        json_objects.append(obj)
                        start = index
                    except json.JSONDecodeError:
                        break

                if json_objects:
                    return {
                        "data": [item['id'] for obj in json_objects for item in obj.get('data', []) if 'id' in item]
                    }

                return {
                    "error": "Failed to parse JSON response",
                    "details": str(e)
                }

            # Check for successful response and extract data
            if response.status == 200 and 'data' in body:
                return {
                    "data": [item['id'] for item in body['data'] if 'id' in item]
                }
            else:
                return {
                    "error": "Unexpected response format or status",
                    "status": response.status,
                    "response": body
                }


@app.post("/runCeligoFlow")
async def run_celigo_flow(data: CeligoFlow):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {data.params.token}"
    }
    url = data.params.url

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{url}/flows/{data.flow_id}/run", headers=headers, ssl=False) as response:
            body = await response.json()
            job_id = body.get('_jobId', None)
            errors = body.get('errors', None)
            if errors is None:
                if job_id is None:
                    return {
                        'status': 'failed',
                        'data': 'Execution Error, Job ID was not retrieved'
                    }
                else:
                    return {
                        'status': 'success',
                        'data': job_id
                    }
            else:
                return {
                    'status': 'failed',
                    'data': errors[0].get('message', 'No returned message.')
                }


@app.post("/getCeligoJobStatus")
async def get_celigo_job_status(data: CeligoJob):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {data.params.token}"
    }
    url = data.params.url

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url}/jobs/{data.job_id}", headers=headers, ssl=False) as response:
            body = await response.json()
            status = body.get('status', None)
            if status is None:
                return {
                    'status': 'failed',
                    'data': 'Execution Error, Job Status was not retrieved.'
                }
            else:
                return {
                    'status': 'success',
                    'data': status
                }
