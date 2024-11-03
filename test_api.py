import os
from dotenv import load_dotenv
from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableClient, UpdateMode
from playwright.sync_api import APIRequestContext, sync_playwright

load_dotenv("cosmosdb.env")

visitor_count = 0
table_name = "Visitor_Counter"
connection_string = os.getenv("COSMOS_DB")

def test_api_create():
    table_client = TableClient.from_connection_string(conn_str=connection_string, table_name=table_name)

    data = {
        "PartitionKey": "Visitors",
        "RowKey": "0.0.0.0",
        "VisitorCount": visitor_count
    }


    table_client.create_entity(entity=data)
    assert True, "Entitiy added successfully"
    print(f"Created entity; {table_client.get_entity(partition_key='Visitors', row_key='0.0.0.0')}")


def test_api_read():
    with sync_playwright() as p:
        request_context: APIRequestContext = p.request.new_context()
    
        response = request_context.get("https://visitor-counter-api-http-trigger.azurewebsites.net/api/visitor_counter")
    
        assert response.status == 200, f"Request failed with status {response.status}" 
    
        data = response.json()
        print("Response:", data)

        assert "VisitorCount" in response.json(), "Missing 'VisitorCount' key in response"

        request_context.dispose()


def test_api_update():
    table_client = TableClient.from_connection_string(conn_str=connection_string, table_name=table_name)

    data = {
        "PartitionKey": "Visitors",
        "RowKey": "0.0.0.0",
        "VisitorCount": visitor_count + 1
    }
    
    table_client.upsert_entity(entity=data, mode=UpdateMode.MERGE)
    assert True, "Entity updated successfully"
    print(f"Updated entity, new value = {table_client.get_entity(partition_key='Visitors', row_key='0.0.0.0')}")


def test_api_delete():
    table_client = TableClient.from_connection_string(conn_str=connection_string, table_name=table_name)

    table_client.delete_entity(partition_key='Visitors', row_key='0.0.0.0')
    print("Entity deleted successfully")

    try:
        table_client.get_entity(partition_key='Visitors', row_key='0.0.0.0')
        assert False, "Entity still exists!"
        
    except ResourceNotFoundError:
        print("Entity not found, as expected")
        assert True