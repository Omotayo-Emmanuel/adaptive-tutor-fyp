
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
