import requests
import time

celigoUrlTest = 'http://127.0.0.1:8000/testCeligoConnection'
celigoUrlExport = 'http://127.0.0.1:8000/runCeligoExport'
celigoUrlFlow = 'http://127.0.0.1:8000/runCeligoFlow'
url ="http://127.0.0.1:8000/getToken"
ship_confirm_url = "http://127.0.0.1:8000/getOrders"
ship_confirm_url_specific = "http://127.0.0.1:8000/getShipmentConfirmation/specific"
ship_confirm_url_no_thread = "http://127.0.0.1:8000/getOrders/nonthread"

myjson = {
    'client_secret': 'fqju**J@U)N^d}`q8tQ',
    'client_id': 'juststeven.capacity.client'
}

shipConfirmPayloadBasic = {
    "key": "CD343BFA-3109-44D6-A4CE-63313F98B8C1",
    "date": "2024-08-01",
    "token": None,
    "batch": 12,
    "is_full_list": False
}

shipConfirmPayload = {
    "key": "CD343BFA-3109-44D6-A4CE-63313F98B8C1",
    "start_date": "2024-07-01",
    "end_date": "2024-07-01",
    "token": None,
    "max_batches": 24
}

# myjson = {
#     'client_secret': '*u6d8ev$0B{qL8B',
#     'client_id': 'lysecomm.capacity.client'
# }

# shipConfirmPayload = {
#     "key": "EDAE07E5-9710-4224-BD37-F95CF39A7151",
#     "start_date": "2024-07-01",
#     "end_date": "2024-07-01",
#     "token": None,
#     "max_batches": 6
# }


specificOrderPayload = {
    "key": "CD343BFA-3109-44D6-A4CE-63313F98B8C1",
    "batch_date": "2024-07-01",
    "batch_number": 12,
    "token": None,
    "order_number": "SO2327741"
}

celigoAuthPayload = {
    'token': '7327f7c2d5334142aabe647663ed6afb',
    'url': 'https://api.integrator.io/v1'
}
celigoExportPayload = {
    'params': {
        'token': 'e0dbc2b44677405499f9237975b758fd',#'e8c6302f965f4095ad3d26d8a8d09a4e',#//'7327f7c2d5334142aabe647663ed6afb',
        'url': 'https://api.integrator.io/v1'
    },
    'export_id': '65de3a85d6d37f343d79a52a'
}
celigoFlowPayload = {
    'params': {
        'token': '7327f7c2d5334142aabe647663ed6afb',
        'url': 'https://api.integrator.io/v1'
    },
    'flow_id': '66819994e4787783082087d7'
}


start_time = time.time()
token = requests.post(url,json=myjson).json()['access_token']
print(token)

if token != "":
     shipConfirmPayloadBasic['token'] = token
     #print(shipConfirmPayload)
     ship_confirm_data = requests.post(ship_confirm_url_no_thread,json=shipConfirmPayloadBasic).json()
     print(ship_confirm_data)
    # specificOrderPayload['token'] = token
    # print(specificOrderPayload)
    # specific_order = requests.post(ship_confirm_url_specific, json=specificOrderPayload)
    # print(specific_order.json())

#print(requests.post(celigoUrl,json=celigoAuthPayload).json())
#print(requests.post(celigoUrlExport,json=celigoExportPayload).json())
#print(requests.post(celigoUrlExport,json=celigoExportPayload).json())

end_time = time.time()
execution_time = end_time - start_time
print(f"Time taken for execution: {execution_time:.2f} seconds")