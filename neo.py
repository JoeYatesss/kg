import re
import json
from neo4j import GraphDatabase
from neo4j import Driver
from dotenv import load_dotenv
import os
from typing import List, Optional, Dict, Any

# OPENAI_API_KEY = "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"
# NEO4J_URI = 'neo4j+s://66f2af96.databases.neo4j.io'
# NEO4J_USER = 'neo4j'
# NEO4J_PASSWORD = 'BgCV_L2ClsBI6AjXl8_P952nAjMaHf21RK3SwbPAyzM'

os.environ['OPENAI_API_KEY'] = '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'
os.environ['NEO4J_URI'] = 'neo4j+s://66f2af96.databases.neo4j.io'
os.environ['NEO4J_USER'] = 'neo4j'
os.environ['NEO4J_PASSWORD'] = 'BgCV_L2ClsBI6AjXl8_P952nAjMaHf21RK3SwbPAyzM'
os.environ['AURA_INSTANCEID'] ='d1492ac2'
os.environ['AURA_INSTANCENAME'] = 'Instance01'

def run_query(driver: Driver, query:str, parameters:Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Executes a Cypher query against the Neo4j database using the provided driver.
    
    Args:
        query (str): The Cypher query to be executed.
        parameters (Optional[Dict[str, Any]]): A dictionary of parameters for the Cypher query.
        driver (Driver): An instance of a Neo4j driver to manage connections to the database.
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents the fields
        of a single record returned by the query.
        
    Raises:
        Exception: If an error occurs during query execution or session management.
    """
    try:
        with driver.session() as session:
            result = session.run(query, parameters)
            return [dict(record) for record in result]
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Load the environment variables from .env file
load_dotenv()

# Use os.environ to access environment variables
NEO4J_URI = os.environ.get('NEO4J_URI')
NEO4J_USERNAME = os.environ.get('NEO4J_USERNAME') # default neo4j
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD') # default neo4j for local instance
AURA_INSTANCEID = os.environ.get('AURA_INSTANCEID')
AURA_INSTANCENAME = os.environ.get('AURA_INSTANCENAME')

def extract_first_json(text):
    # Regex pattern to find the first instance of a JSON object or array
    json_pattern = r'(\{.*?\}|\[.*?\])'
    
    # Using non-greedy matching to capture the smallest possible valid JSON string
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            # Convert the JSON string to a Python dictionary or list
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError:
            print("Found string is not a valid JSON.")
    else:
        print("No JSON object or array found in the text.")

# Example usage
openai_api_response_text = '''
    Here is a JSON object: [{"name":"Chelsea", "description": "Football Club"}, {"name":"Player", "description":"Football Player"}, {"name":"Coach", "description":"Football Team Coach"}, {"name":"Stadium", "description":"Football Stadium"}]
    Let me know if you need any more help
    Yours truly,
    OpenAI
    P.S. Big Brother is watching you
'''
openai_reposponse_json = extract_first_json(openai_api_response_text)

print(openai_reposponse_json)

# Replace these with your Aura or Neo4j connection details or use the values loaded from environment variables.
uri = NEO4J_URI
username = NEO4J_USERNAME
password = NEO4J_PASSWORD

# Create a driver instance
driver = GraphDatabase.driver(uri, auth=(username, password))

# 4. Empty database for a clean test
from neo4j import GraphDatabase

# Replace these with your Aura connection details
uri = NEO4J_URI
username = NEO4J_USERNAME
password = NEO4J_PASSWORD

class DatabaseCleaner:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def reset_database(self):
        with self.driver.session() as session:
            session.write_transaction(self._delete_all)

    @staticmethod
    def _delete_all(tx):
        tx.run("MATCH (n) DETACH DELETE n")

if __name__ == "__main__":
    db_cleaner = DatabaseCleaner(uri, username, password)
    db_cleaner.reset_database()
    db_cleaner.close()
    print("Database has been reset to a blank state.")

# 5. Load JSON you got from the API response as a bunch of entities in Neo4j

for entity_and_description_pair in openai_reposponse_json:
    # create the first entity
    entity_name = entity_and_description_pair["name"]
    entity_description = entity_and_description_pair["description"]
    neo4j_cyper_query = f'CREATE ({entity_name}:Entity {{name: "{entity_name}", description: "{entity_description}"}})'
    print(neo4j_cyper_query)
    results = run_query(driver, neo4j_cyper_query)
    print(results)

# check the database is empty
query = "MATCH (n) RETURN n LIMIT 5"
results = run_query(driver, query)
print('you should see the output is empty, e.g. "[ ]" \nOtherwise see the code for database cleanup at the bottom of this notebook')
print(results)
