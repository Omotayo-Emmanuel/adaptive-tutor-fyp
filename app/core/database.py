# Import Libraries
import os
import sys
import certifi
from pymongo import MongoClient
from neo4j import GraphDatabase
from pymongo.errors import ConnectionFailure
from neo4j.exceptions import ServiceUnavailable

# Ensuring Python can find the "app" module when running this file directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
# Importing settings from config.py
from app.core.config import settings

# MongoDB Connection Setup
class MongoDBClient:
    def __init__(self):
        self.client = None
        self.db = None
    
    def connect(self):
        try:
            self.client = MongoClient(settings.MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
            self.db = self.client[settings.MONGO_DB_NAME]
            # Ping the database to verify the connection
            self.client.admin.command('ping')
            return True
        except ConnectionFailure as e:
            print(f"MongoDB Connection Failed: {e}")
            return False

#  Instantitate the Mongo client
mongodb = MongoDBClient()

# Neo4j Connection Setup
class Neo4jClient:
    def __init__(self):
        self.driver = None
    
    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI, 
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )
            # Verify the connection by opening a session
            self.driver.verify_connectivity()
            return True
        except ServiceUnavailable as e:
            print(f"Neo4j Connection Failed: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during Neo4j connection: {e}")
            return False
        
    def close(self):
        if self.driver is not None:
            self.driver.close()

# Instantiate the Neo4j client
neo4j_db = Neo4jClient()


# --- Optional: Quick Validation Check ---

if __name__ == "__main__":
    print("Testing database connections... \n")
    
    # Test MongoDB Connection
    print("Attempting to connect to MongoDB Atlas...")
    if mongodb.connect():
        print("✅ MongoDB Atlas connection successful!")
    else:
        print("❌ MongoDB Atlas connection failed. Check your MONGO_URI and network settings.")
    print("\n-----------------------------\n")
    
    
    # Test Neo4j Connection
    print("Attempting to connect to Neo4j AuraDB...")
    if neo4j_db.connect():
        print("✅ Neo4j AuraDB connection successful!")
        neo4j_db.close()
    else:
        print("❌ Neo4j AuraDB connection failed. Check your NEO4J_URI, credentials, and network settings.")

    