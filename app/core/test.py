
# --- Optional: Quick Validation Check ---
# When you run this file directly, it will verify that the keys were loaded.
if __name__ == "__main__":
    print(f"Loading configurations for: {settings.PROJECT_NAME}")
    if not settings.GEMINI_API_KEY:
        print("❌ Warning: GEMINI_API_KEY not found. Check your .env file.")
    else:
        print("✅ Gemini API Key loaded successfully.")
        
    if not settings.MONGO_URI:
        print("❌ Warning: MONGO_URI not found.")
    else:
        print("✅ MongoDB URI loaded successfully.")
        
    if not settings.NEO4J_PASSWORD:
        print("❌ Warning: NEO4J_PASSWORD not found.")
    else:
        print("✅ Neo4j Credentials loaded successfully.")



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

    