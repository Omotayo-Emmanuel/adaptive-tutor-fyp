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
    
    