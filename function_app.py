import azure.functions as func
import os
import json
from azure.data.tables import TableClient, UpdateMode

connection_string = os.getenv("CosmosDbConnectionSetting")

# Static variables outside of HttpTrigger - improved speed by about 80%
table_name = "Visitor_Counter"
table_client = TableClient.from_connection_string(conn_str=connection_string, table_name=table_name)

# Static partition key
partition_key = "Visitors"

app = func.FunctionApp()

@app.route(route="visitor_counter", auth_level=func.AuthLevel.ANONYMOUS)

def visitor_counter(req: func.HttpRequest) -> func.HttpResponse:

    # Static variables
    entities = {entity['RowKey']: entity for entity in table_client.list_entities()}
    # Get max_visitor_count
    max_visitor_count = max((int(entity["VisitorCount"]) for entity in entities.values()),default = 0)

    # Get client IP
    visitor_ip = req.headers.get('X-Forwarded-For')
    if not visitor_ip:
        visitor_ip = req.headers.get('X-Original-For') or req.headers.get('REMOTE_ADDR')
        if not visitor_ip:
            visitor_ip = "Unknown IP"

    if ':' in visitor_ip:
        visitor_ip = visitor_ip.split(':')[0] # grab 0 for ip-address - 1 for port-nr
         
    if visitor_ip in entities:
        max_visitor_count_same = entities[visitor_ip]['VisitorCount']

        # Retrieve the existing entity
        existing_entity = {
            'PartitionKey': partition_key,
            'RowKey': entities[visitor_ip]['RowKey'],
            'VisitorCount': max_visitor_count_same
        }
        print(f"Updated entity: {existing_entity}")
        # Upsert the updated entity
        table_client.upsert_entity(entity=existing_entity, mode=UpdateMode.MERGE)
    else:
        # Increment visitor_count
        max_visitor_count += 1

        # Create a new entity for a new visitor
        new_entity = {
            'PartitionKey': partition_key,
            'RowKey': visitor_ip,
            'VisitorCount': max_visitor_count
        }
        print(f"Created entity: {new_entity}")
        # Insert the new entity
        table_client.upsert_entity(entity=new_entity, mode=UpdateMode.MERGE)

    json_response = json.dumps({"VisitorCount": max_visitor_count})

    return func.HttpResponse(json_response, headers={"Content-Type": "application/json"}, status_code=200)