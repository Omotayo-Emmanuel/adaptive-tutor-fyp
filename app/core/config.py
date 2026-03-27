import os
from dotenv import load_dotenv

# Loading environment mvarriables fromt the .env file 
# located in the root directory
load_dotenv()

class Settings:
    """
    Centralized configuration class for the Adaptive Intelligent Tutoring System.
    Retrieves and stores all neccessary API keys and connection strings. 
    """
    # Project Information
    PROJECT_NAME: str = "Adaptive Tutor API"
    
    # API Keys and Connection Strings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    
    # MongoDB Connection String
    MONGO_URI: str = os.getenv("MONGO_URI")
    MONGO_DB_NAME: str = os.getenv("MONGODB_NAME", "adaptive_tutor_db")
    
    # Neo4j AuraDB (Graph Database) Connection Details
    NEO4J_URI: str = os.getenv("NEO4J_URI")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD")
    
    # Azure OpenAI (For Human-in-the-Loop Feedback / RL Agent Fallback)
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT : str = os.getenv("AZURE_OPENAI_ENDPOINT")
    
# Instantiate the settings object to be used across the application
settings = Settings()
