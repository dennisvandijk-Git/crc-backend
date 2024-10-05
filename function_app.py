import azure.functions as func
import os
import datetime
from azure.data.tables import TableClient

connection_string = os.getenv("CosmosDbConnectionSetting")

# Static variables outside of HttpTrigger - improved speed by about 80%
table_name = "visitorCount"
table_client = TableClient.from_connection_string(conn_str=connection_string, table_name=table_name)
entities = list(table_client.list_entities())  # Convert to list

app = func.FunctionApp()

@app.route(route="http_trigger_visitor_counter", auth_level=func.AuthLevel.ANONYMOUS)

def http_trigger_visitor_counter(req: func.HttpRequest) -> func.HttpResponse:

    # Static variables
    date = str(datetime.datetime.now())

    # Get client IP
    visitor_ip = req.headers.get('X-Forwarded-For')
    if not visitor_ip:
        visitor_ip = req.headers.get('X-Original-For') or req.headers.get('REMOTE_ADDR')
        if not visitor_ip:
            visitor_ip = "Unknown IP"

    if ':' in visitor_ip:
        visitor_ip = visitor_ip.split(':')[0] # grab 0 for ip-address - 1 for port-nr

    # Empty list for UnboundLocalError
    ip_addresses = []

    # Get the maximum visitor count and IP addresses
    if entities:
        max_visitor_count = max(int(entity["VisitorCount"]) for entity in entities)
        ip_addresses = [entity["RowKey"] for entity in entities]
    else:
        max_visitor_count = 0
        table_client.create_entity(entity={
            'PartitionKey': date,
            'RowKey': visitor_ip,
            'VisitorCount': max_visitor_count
        })

    if visitor_ip in ip_addresses:
        # Existing IP, no increment - store current max
        table_client.create_entity(entity={
            'PartitionKey': date,
            'RowKey': visitor_ip,
            'VisitorCount': max_visitor_count
        })
        
    else:
        # New visitor, increment the count + 1
        max_visitor_count += 1
        table_client.create_entity(entity={
            'PartitionKey': date,
            'RowKey': visitor_ip,
            'VisitorCount': max_visitor_count
        })

    return func.HttpResponse(str(max_visitor_count), status_code=200)