# gets a call from the frontend
# 1. check if the query is related to the database or general data related
# 2. if yes, then check get table schema embedding from vector db, ask llm for a sql query
# 2.1. run the sql query and get the result
# 2.2. if the result is empty, ask llm for a better query
# 2.3. if the result is not empty, return the result to the frontend
# 3. if no, query llm directly, return response to frontend
 
import os
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from pydantic import BaseModel
import mysql.connector
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from chromadb import HttpClient
from typing import Any 
# MySQL config
load_dotenv()

db_config = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE")
}  


app = FastAPI()

# Global shared resources
chroma_client = None
schema_collection = None

# LLM config
llm = OllamaLLM(base_url="http://dg-ollama:11434", model="mistral")
embedder = OllamaEmbeddings(base_url="http://dg-ollama:11434", model="nomic-embed-text")

# MySQL config
db_config = {
    "host": "dg-db",
    "user": "genie",
    "password": "magic",
    "database": "datagenie"
}

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_answer(request: PromptRequest):
    global chroma_client, schema_collection
    # Step 0: Check if Chroma is initialized
    prompt = request.prompt
    print(f"Received prompt: {prompt}")
    # Step 1: Determine if the query is DB-related
    check_query= f""" 
        system: You are a query classifier that categorizes questions into three types.
        Users are expected to ask questions about various tables in our database - has customer, loan and credit transaction information.
        However, they may also ask general questions that relate to data analysis.
        Respond in JSON format matching this schema:
        {{
        "queryType": "SQL" | "General"  
        }},
            user: Classify this question: ${prompt}
        
    """
    query_type_json = llm.invoke(check_query).strip()
    print(f"Query Type: {query_type_json}")
    import json
    try:
        parsed = json.loads(query_type_json)
        query_type = parsed.get("queryType")
    except Exception as e:
            return {"response": f"❌ Failed to parse LLM response as JSON: {str(e)}", "raw": response_json}
        

    #query_type = "SQL" # For testing purposes, assume all queries are SQL-related
    if query_type == "SQL":
        # Step 2: Init Chroma if not yet done
        if not chroma_client:
            try:
                chroma_client = HttpClient(host="dg-vector", port=8001)
                schema_collection = chroma_client.get_or_create_collection(name="db_schema")
            except Exception as e:
                return {"response": f"❌ Could not connect to Chroma: {str(e)}"}

        # Step 2: Embed prompt and do similarity search
        embedded_prompt = embedder.embed_query(prompt)
        docs = schema_collection.query(query_embeddings=[embedded_prompt], n_results=3)

        if not docs.get("documents") or not docs["documents"][0]:
            return {"response": "❌ No matching schema found in Chroma DB. Please ensure schema is embedded."}

        related_schema = docs["documents"][0][0]

        # Step 2.1: Ask LLM to write SQL
        sql_prompt = f"""
            You are a mysql query generator. Follow these rules:
            1. Generate precise, efficient mysql-compliant queries based on schema analysis.
            2. When necessary, use the relationships array to join tables.
            5. Use a maximum limit of 1000 whenever a limit is not specified.
            6. Always use the column names provided in the schema and never reference columns outside of that.
            7. Use mysql-specific features when appropriate.
            8. Make sure that the query fully answers the user's question.

            Respond in JSON format matching this schema:
            {{
              "query": "string",
              "explanation": "string"
            }}

            User: Using this schema analysis {related_schema}, generate a mysql SQL query FOR: {prompt}
            """
       #sql_prompt = f"\nWrite a SQL query for mysql to answer: {prompt}. Give me only the sql query to run, no explainations"
        
        try:
            
            response_json = llm.invoke(sql_prompt)
            print(f"SQL LLM Response: {response_json}")
            import json
            try:
                parsed = json.loads(response_json)
                sql = parsed.get("query")
                explanation = parsed.get("explanation", "")
            except Exception as e:
                return {"response": f"❌ Failed to parse LLM response as JSON: {str(e)}", "raw": response_json}
        except Exception as e:
            return {"response": f"❌ Failed to generate SQL query: {str(e)}"}

        #sql = llm.invoke(sql_prompt)
        print(f"Generated SQL: {sql}")
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)
            result = cursor.fetchall()

            # Step 2.2: If empty, retry with refined query (up to 2 more times)
            retries = 0
            while not result and retries < 2:
                retry_prompt = f"That query returned no results. Try a different SQL query for mysql using the same context: {related_schema}\nOriginal question: {prompt}, give me only the query to run, no explainations"
                
                sql = llm.invoke(retry_prompt)
                print(f"Retry SQL: {sql}")
                cursor.execute(sql)
                result = cursor.fetchall()
                retries += 1

            cursor.close()
            conn.close()

            if not result:
                return {"response": "No results found after multiple attempts."}
            return {"data": result}

        except Exception as e:
            return {"response": f"Error processing SQL: {str(e)}"}

    else:
        # Step 3: General LLM response
        answer = llm.invoke(prompt)
        return {"response": answer}

@app.get("/table/{table_name}")
async def get_table_data(table_name: str):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
        result = cursor.fetchall()
        cursor.close()
        conn.close()

        return {"rows": result}
    except Exception as e:
        return {"error": f"Failed to fetch table data: {str(e)}"}
    
@app.on_event("startup")
def startup_event():
    # Initialize Chroma and embed schema on startup
    print("Initializing Chroma and embedding schema...")
    global chroma_client, schema_collection
    try:
        chroma_client = HttpClient(host="dg-vector", port=8000)
        schema_collection = chroma_client.get_or_create_collection(name="db_schema")
        embed_schema_to_chroma()
        print(f"🔢 Total documents in Chroma DB: {schema_collection.count()}")

    except Exception as e:
        print(f"❌ Could not initialize Chroma or embed schema: {str(e)}")



# Function to embed schema into Chroma
def embed_schema_to_chroma():
    global schema_collection
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
        """, (db_config["database"],))

        schema = {}
        for table, col, dtype in cursor.fetchall():
            schema.setdefault(table, []).append(f"{col} ({dtype})")

        docs = []
        ids = []

        for table, fields in schema.items():
            doc = f"Table '{table}' contains: " + ", ".join(fields) + "."
            docs.append(doc)
            ids.append(f"table_{table}")

        if schema_collection.count() > 0:
            print("🟡 Vector DB already initialized. Skipping embedding.")
            return

        vectors = embedder.embed_documents(docs)
        schema_collection.add(documents=docs, embeddings=vectors, ids=ids)
        print("✅ Schema embedded into Chroma DB via dg-vector HTTP API!")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to embed schema into Chroma: {str(e)}")
