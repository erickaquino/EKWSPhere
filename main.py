import asyncio
import json
import time
import configparser
import os
from netsuite import NetSuite, Config, TokenAuth
from urllib.parse import urlparse


def load_config():
    config_parser = configparser.ConfigParser()
    config_parser.read(os.path.join(os.getcwd(), 'config.ini'))
    return {
        'account': config_parser.get('auth', 'account'),
        'consumer_key': config_parser.get('auth', 'consumer_key'),
        'consumer_secret': config_parser.get('auth', 'consumer_secret'),
        'token_id': config_parser.get('auth', 'token_id'),
        'token_secret': config_parser.get('auth', 'token_secret'),
        'script_id': int(config_parser.get('restlet', 'script_id')),
        'deployment': int(config_parser.get('restlet', 'deployment')),
        'suiteQLConcurrency': int(config_parser.get('concurrency', 'limit'))
    }

config_values = load_config()
config = Config(
    account=config_values['account'],
    auth=TokenAuth(
        consumer_key=config_values['consumer_key'],
        consumer_secret=config_values['consumer_secret'],
        token_id=config_values['token_id'],
        token_secret=config_values['token_secret']
    ),
)
ns = NetSuite(config)

async def post_request(payload, semaphore, concurrency):
    async with semaphore:
        start_time = time.time()
        response = await ns.restlet.post(config_values['script_id'], deploy=config_values['deployment'], json=payload)
        execution_time = time.time() - start_time
        print(f"Payload: {payload}, Concurrency: {concurrency}, Execution time: {execution_time:.2f} seconds")
        return response
async def run_query(query):
    final_query = {"q": query}
    headers = {'prefer': 'transient'}
    arr_values = []
    start_time = time.time()

    rest_api_results = await ns.rest_api.post('/query/v1/suiteql', headers=headers, json=final_query)
    total_results = rest_api_results.get('totalResults', 0)
    arr_values.extend([data.pop('links', None) or data for data in rest_api_results['items']])

    if total_results > 1000:
        offset = 1000
        tasks = []

        while offset < total_results:
            tasks.append(sub_query(f'/query/v1/suiteql?limit=1000&offset={offset}', final_query))
            offset += 1000

        results = await asyncio.gather(*tasks)
        for result in results:
            arr_values.extend([data.pop('links', None) or data for data in result['items']])

    print(f"TOTAL Execution time: {time.time() - start_time:.2f} seconds")
    print("Total # of retrieved data: " + str(len(arr_values)))
    print(arr_values)

    if input('Continue (y/n): ').lower() == 'y':
        concurrency = int(input('Enter # of concurrent requests: '))
        semaphore = asyncio.Semaphore(concurrency)
        start_time = time.time()

        tasks = [post_request({"soID": item['id']}, semaphore) for item in arr_values]
        results = await asyncio.gather(*tasks)

        print(f"Execution time: {time.time() - start_time:.2f} seconds")
        print(results)
    else:
        print('Exit.')
async def sub_query(url, query):
    headers = {'prefer': 'transient'}
    async with asyncio.Semaphore(config_values['suiteQLConcurrency']):
        response = await ns.rest_api.post(url, headers=headers, json=query)
    return response
async def async_main(field):
    query = f"SELECT {field} from TRANSACTION where type = 'SalesOrd'"
    final_query = {"q": query}
    headers = {'prefer': 'transient'}
    rest_api_results = await ns.rest_api.post("/query/v1/suiteql", headers=headers, json=final_query)
    print(rest_api_results)
    data = [item[field] for item in rest_api_results['items']]
    print(data)


if __name__ == "__main__":
    response = input('Query to run: ')
    asyncio.run(run_query(response))
    # Uncomment below lines to run async_main function if needed
    # fld = input('Field to get: ')
    # asyncio.run(async_main(fld))
