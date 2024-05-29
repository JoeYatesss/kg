import streamlit as st
import openai
from neo4j import GraphDatabase
from neo4j import GraphDatabase, Driver
import json
from typing import Any, Dict, List, Optional

OPENAI_API_KEY = ''
NEO4J_URI = 'neo4j+s://d1492ac2.databases.neo4j.io'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'qzd-MALJS8FZ8u3hQ9rxQPDusYjulQ-cryWx0sIC6rM'
AURA_INSTANCEID ='d1492ac2'
AURA_INSTANCENAME = 'Instance01'
# Replace these with your Aura or Neo4j connection details or use the values loaded from environment variables.
uri = NEO4J_URI
username = NEO4J_USER
password = NEO4J_PASSWORD
openai.api_key= OPENAI_API_KEY

# Database Connection
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
# Function Definitions
def run_query(driver: GraphDatabase.driver, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    try:
        with driver.session() as session:
            result = session.run(query, parameters)
            return [dict(record) for record in result]
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def sanitize_label(label: str) -> str:
    """Sanitize the label to ensure it is a valid Neo4j label by replacing spaces with underscores and ensuring it starts with a letter."""
    sanitized_label = label.replace(" ", "_")
    if re.match(r'^\d', sanitized_label):
        sanitized_label = 'E_' + sanitized_label  # Prefix with 'E_' if it starts with a number
    return sanitized_label

def extract_entities_and_relationships(text):
    try:
        # Fixed prompt
        prompt = (
            "Extract the entities and their relationships from the following text. "
            "For each entity, replace spaces with underscores in the entity names and generate a Cypher CREATE query for Neo4j with the format: "
            "CREATE (EntityName:Entity {name: 'EntityName', description: 'EntityDescription'}). "
            "For relationships, use the format: "
            "(Entity1)-[:RELATIONSHIP_TYPE]->(Entity2). "
            "Return the result in JSON format with 'entities' and 'relationships' keys. "
            "Ensure there are no spaces in the entity names, replace them with underscores. "
            "Also, ensure entity names do not start with a number by prefixing such names with 'E_'.\n\n"
            f"Text:\n{text}\n\n"
            "Example response:\n"
            "{\n"
            '  "entities": [\n'
            '    {"name": "Chelsea", "description": "Football Club"},\n'
            '    {"name": "Player", "description": "Football Player"},\n'
            '    {"name": "Coach", "description": "Football Team Coach"},\n'
            '    {"name": "Stadium", "description": "Football Stadium"}\n'
            '  ],\n'
            '  "relationships": [\n'
            '    {"from": "Player", "to": "Chelsea", "type": "PLAYS_FOR"},\n'
            '    {"from": "Coach", "to": "Chelsea", "type": "COACHES"},\n'
            '    {"from": "Chelsea", "to": "Stadium", "type": "PLAYS_AT"}\n'
            '  ]\n'
            '}'
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract entities and relationships from the text and generate Cypher queries for Neo4j."},
                {"role": "user", "content": prompt}
            ]
        )

        response_content = response['choices'][0]['message']['content']
        st.write("OpenAI Response:", response_content)  # Display the OpenAI response in Streamlit

        json_data = extract_first_json(response_content)
        if json_data:
            # Generate Cypher queries for entities and relationships
            queries = []
            for entity in json_data.get("entities", []):
                sanitized_name = sanitize_label(entity['name'])
                entity_query = f"CREATE ({sanitized_name}:Entity {{name: '{sanitized_name}', description: '{entity['description']}'}})"
                st.write(entity_query)  # Display each query in Streamlit
                queries.append(entity_query)

            for relationship in json_data.get("relationships", []):
                sanitized_from = sanitize_label(relationship['from'])
                sanitized_to = sanitize_label(relationship['to'])
                relationship_query = f"MATCH (a:Entity {{name: '{sanitized_from}'}}), (b:Entity {{name: '{sanitized_to}'}}) CREATE (a)-[:{relationship['type']}]->(b)"
                st.write(relationship_query)  # Display each query in Streamlit
                queries.append(relationship_query)

            # Save response and queries to a JSON file
            with open('cypher_queries.json', 'w') as json_file:
                json.dump({'queries': queries}, json_file, indent=4)
            return queries
        return []
    except Exception as e:
        st.error(f"Error querying OpenAI: {e}")
        return []

def read_text_file(uploaded_file):
    """Read text data from an uploaded file."""
    try:
        text_data = uploaded_file.getvalue().decode("utf-8")
        return text_data
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def chat_with_document(text):
    """Function to handle chat with the document using OpenAI."""
    query = st.text_input("Enter your question below:")
    if query and st.button("Submit"):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Answer this question based on the provided document content:"},
                    {"role": "user", "content": query},
                    {"role": "system", "content": text}
                ]
            )
            response_content = response['choices'][0]['message']['content']
            st.write(response_content)  # Display the OpenAI response in Streamlit
            with open('openai_chat_response.json', 'w') as json_file:
                json.dump({'response': response_content}, json_file, indent=4)
        except Exception as e:
            st.error(f"Error in answering the question: {e}")

def extract_first_json(text):
    '''Extract the first JSON from the response text.'''
    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        return json.loads(text[start:end])
    except ValueError:
        return None

def execute_queries_from_json(json_data):
    """Load Cypher queries from a JSON data and execute them in Neo4j."""
    queries = json_data.get('queries', [])
    if not queries:
        st.error("No queries found in the JSON file.")
        return

    uri = NEO4J_URI
    username = NEO4J_USER
    password = NEO4J_PASSWORD
    driver = GraphDatabase.driver(uri, auth=(username, password))
    try:
        with driver.session() as session:
            for query in queries:
                if query:  # Check if it's not an empty list
                    session.run(query)
                    st.write(f"Executed query: {query}")
        driver.close()
    except Exception as e:
        st.error(f"Failed to execute Cypher queries: {e}")
        if driver:
            driver.close()

def main():
    st.title('Knowledge Graph Creator with OpenAI Integration')

    page = st.selectbox("Select Page", ["Generate Cypher Queries", "Execute Cypher Queries"])

    if page == "Generate Cypher Queries":
        uploaded_file = st.file_uploader("Choose a text file", type=["txt"], key="unique_file_uploader_2")
        if uploaded_file:
            text_data = read_text_file(uploaded_file)
            if text_data:
                cypher_queries = extract_entities_and_relationships(text_data)
                if cypher_queries:
                    with open('cypher_queries.json', 'w') as json_file:
                        json.dump({'queries': cypher_queries}, json_file, indent=4)
                    st.write("Cypher queries have been saved to cypher_queries.json")
                else:
                    st.error("No Cypher queries were generated.")
            else:
                st.error("No text data found in the uploaded file.")

    elif page == "Execute Cypher Queries":
        uploaded_json_file = st.file_uploader("Choose a JSON file with Cypher queries", type=["json"], key="unique_file_uploader_3")
        if uploaded_json_file:
            try:
                json_bytes = uploaded_json_file.read()  # Read the file content as bytes
                json_str = json_bytes.decode('utf-8')  # Decode the bytes to string
                json_data = json.loads(json_str)  # Parse the string to JSON

                # Ensure the JSON data is a dictionary
                if isinstance(json_data, dict):
                    execute_queries_from_json(json_data)
                else:
                    st.error("Invalid JSON structure: expected a dictionary.")
            except Exception as e:
                st.error(f"Error reading JSON file: {e}")

if __name__ == "__main__":
    main()
