import azure.functions as func
import os
import json
import requests
import datetime
from azure.data.tables import TableClient

app = func.FunctionApp()

@app.function_name('HttpAccess')
@app.route(route="access-key", auth_level=func.AuthLevel.ANONYMOUS)

def access_key(req: func.HttpRequest) -> func.HttpResponse:

    real_function_url = "https://visitor-counter-api-http-trigger.azurewebsites.net/api/http_trigger_visitor_counter"

    api_key = os.getenv("API_KEY")

    headers = {
        'x-functions-key': api_key,
        'Content-Type': 'application/json'
    }

    real_function_response = requests.get(real_function_url, headers=headers)
    print(type(real_function_response))
    # print(json.dumps(real_function_response))
    responze = [{"visitsCount": real_function_response.json()}]
    # print(responze)
    # print(json.dumps(responze))

    return func.HttpResponse(
        json.dumps(responze),
        status_code=real_function_response.status_code,
        mimetype="application/json"
    )

@app.route(route="http_trigger_visitor_counter", auth_level=func.AuthLevel.FUNCTION)

def http_trigger_visitor_counter(req: func.HttpRequest) -> func.HttpResponse:
    connection_string = os.getenv("CosmosDbConnectionSetting")

    visitor_ip = req.headers.get('X-Forwarded-For')
    if not visitor_ip:
        visitor_ip = req.headers.get('X-Original-For') or req.headers.get('REMOTE_ADDR')
        if not visitor_ip:
            visitor_ip = 'Unknown IP'
    
    if ':' in visitor_ip:
        visitor_ip = visitor_ip.split(':')[0]

    date = str(datetime.datetime.now())

    table_name = "visitorCount"

    table_client = TableClient.from_connection_string(conn_str=connection_string, table_name=table_name)

    entities = list(table_client.list_entities())  # Convert to list
    if not entities:
        first_visitor = 1
        table_client.create_entity(entity={
            'PartitionKey': date,
            'RowKey': visitor_ip,
            'VisitorCount': first_visitor
        })
        response_json = json.dumps(first_visitor)
        return func.HttpResponse(response_json, mimetype="application/json", status_code=200)
    
    # Get the maximum visitor count and IP addresses
    max_visitor_count = max(int(entity["VisitorCount"]) for entity in entities)
    ip_addresses = [entity["RowKey"] for entity in entities]

    if visitor_ip in ip_addresses:
        # do this - no increment
        table_client.create_entity(entity={
            'PartitionKey': date,
            'RowKey': visitor_ip,
            'VisitorCount': max_visitor_count
        })
        # response_kvp = [{"visitCount": max_visitor_count}]
        # response_json = json.dumps(response_kvp)
        response_json = json.dumps(max_visitor_count)
        return func.HttpResponse(response_json, mimetype="application/json", status_code=200)
    else:
        # do this - increment count + 1
        increment_visitor_count = max_visitor_count + 1
        table_client.create_entity(entity={
            'PartitionKey': date,
            'RowKey': visitor_ip,
            'VisitorCount': increment_visitor_count
        })
        # response_kvp = [{"visitCount": increment_visitor_count}]
        # response_json = json.dumps(response_kvp)
        response_json = json.dumps(max_visitor_count)
        return func.HttpResponse(response_json, mimetype="application/json", status_code=200)