import os
import sys
import uuid
import json
import fitz # PyMuPDF: the Library used to read the raw text from the PDF documents.
import time
from google import genai
from  google.genai import types
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- ENVIRONMENT SETUP ---
# Load parent directory to sys.path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.core.config import settings
from app.models.schemas import DocumentChunk, ConceptNode, ConceptRelationship
from app.core.database import mongodb, neo4j_db

# --- Configuration for Gemini API ---
# Securely load the Gemini API key from environment variables or configuration settings
client  = genai.Client(api_key=settings.GEMINI_API_KEY)

# A temporary blueprint.
# Giving this to Gemini, The AI is forced to return a perfrectly formatted JSON output 
# instead of a messy text paagraph.

class LLMExtraction(BaseModel):
    """
    Schema for the structured knowledge extracted by Gemini from the textbook.
    This will be used to store the extracted concepts and relationships in the Knowledge Graph.
    """
    primary_concept: str
    difficulty_level: str
    nodes: List[ConceptNode]
    relationships: List[ConceptRelationship]
    
# Pipeline Functions
def process_pdf(file_path: str) -> list[str]:
    """
    Reads a PDF file and extracts its raw text content.
    Args:
        file_path (str): The path to the PDF file.
    """
    print(f" Reading PDF: {file_path}")
    
    # Open the PDF file using fitz (PyMuPDF)
    doc = fitz.open(file_path)
    full_text = ""
    
    # Loop through every single page and extract all the text into one giant string.
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        full_text += str(page.get_text("text")) + "\n"  # Add a newline after each page's text
        
    print(f" Extracted text length: {len(full_text)} characters")
    print(" Chunking text...")
    
    # We cannot send a 50-page string to the database. We use LangChain to split it.
    # Chunk_size=1000: Each piece will be roughly 1,0000 characters.
    # chunk_overlap=150: The last 150 characters of Chunk 1 become the first 150 
    # characters of Chunk 2. This overlap helps maintain context across chunks, preventing a sentence from being cut in half
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators= ["\n\n", "\n", ".", " ", ""]
        )
    
    chunks = splitter.split_text(full_text)
    print(f" Created {len(chunks)} chunks.")
    return chunks

def  analyze_and_embed(chunk_text: str) -> tuple[list, dict]:
    """
    Uses Gemini to analyze a chunk of text and extract structured knowledge, including the primary concept, difficulty level, and relationships.
    Args:
        chunk_text (str): The text content of the chunk to be analyzed.
    Returns:
        LLMExtraction: A structured representation of the extracted knowledge, including the primary concept, difficulty level, and relationships.
    """
    
    # Action A: Create the vector Embedding (For MongoDB)
    # Gemini's embedding model to turn the English text into a list of numbers.
    # This allows for "Semantic Search" (finding answers by meaning, not just keywords).
    embedding_result = client.models.embed_content(
        model = "gemini-embedding-2-preview",
        contents = chunk_text
    )
    vector = embedding_result.embeddings[0].values
    
    # Action B: Extract the structured knowledge (For Neo4j)
    # We prompt Gemini to act as a teacher, read the chunk, and map out the concepts.'
    prompt = f"""
    Analyze the following academic text chunk.
    1. Identify the primary educational concept.
    2. Assess the difficulty level (Beginner, Intermediate, Advanced).
    3. Extract key concepts (nodes) and their relationships (edges).
    
    Text: {chunk_text}
    """
    
    # We pass our LLMExtraction schema here to guarantee the output is strict JSON.
    # temperature = 0.1 ensures the AI styas highly factual and doesn't hallucinate.
    response = client.models.generate_content(
        model = "gemini-3.1-flash-lite-preview",
        contents = prompt,
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema = LLMExtraction, # This tells Gemini to format its response according to the LLMExtraction schema we defined earlier.
            temperature=0.1
        )
    )
    
    # Convert the AI's string response into into a usuable Python dictionary
    extraction = json.loads(response.text)
    return vector, extraction

def ingest_to_databases(chunk_text: str, vector: list, extraction:dict, source_file: str) -> None:
    """
    Ingests the processed chunk text, vector embedding, and extracted knowledge into the databases.
    Args:
        chunk_text (str): The text content of the chunk.
        vector (list): The vector embedding of the chunk.
        extraction (dict): The structured knowledge extracted from the chunk.
        source_file (str): The path to the source file.
    
    returns:
        None
    """    
    # Generate a random, unique ID for this specific paragraph of text
    chunk_id = str(uuid.uuid4())
    
    # -- Ingest into MongoDB Atlas (Vector Database) --
    # package the chunk text, vector, and metadata into a DocumentChunk schema
    chunk_doc = DocumentChunk(
        chunk_id = chunk_id,
        text_content = chunk_text,
        source_file = source_file,
        primary_concept = extraction["primary_concept"],
        difficulty_level = extraction["difficulty_level"],
        embedding = vector
    )
    
    # Connect to the "course_chunks" collection in Atlas and save it
    if mongodb.db is None:
        raise RuntimeError("MongoDB connection not initialized. Ensure mongodb.connect() was called.")
    collection = mongodb.db["course_chunks"]
    collection.insert_one(chunk_doc.model_dump())
    
    # -- Ingest into Neo4j (Knowledge Graph) --
    # Connect to Neo4j and create nodes and relationships based on the extracted knowledge
    with neo4j_db.driver.session() as session:
        # Create the Nodes (The concept)
        for node in extraction["nodes"]:
            # We use MERGE instead of CREATE, MERGE checks if the concept (e.g., "Recursion") 
            # already exists in the graph. If it does, it reuses that node instead of creating a duplicate. 
            # This keeps our graph clean and efficient.
            session.run("""
                MERGE (c:Concept {name: $name})
                ON CREATE SET c.concept_type = $concept_type, c.description = $description
            """,
            name = node["name"],
            concept_type = node["concept_type"],
            description = node.get("description", "") )
            
        # Create the Relationships (How the concepts are connected)
        for rel in extraction["relationships"]:
            # Draw a directional line between two concepts (e.g., "Recursion" -> "IS_A" -> "Programming Paradigm")
            rel_type = rel["relation_type"].upper().replace(' ', '_')
            session.run(f"""
                MATCH (source: Concept {{name: $source_name}})
                MATCH (target: Concept {{name: $target_name}})
                MERGE (source)-[r: {rel_type}]->(target)
                ON CREATE SET r.description = $description
            """,
            source_name = rel["source"],
            target_name = rel["target"],
            description = rel.get("description", ""))
            
    
# Exection Pipeline
def run_pipeline(file_path: str) -> None:
    """
    Executes the entire RAG pipeline: processing the PDF, analyzing and embedding chunks, and ingesting into databases.
    Args:
        file_path (str): The path to the PDF file to be processed.
    Returns:
        None
    """
    # locate the PDF in the data folder
    # file_path = os.path.join(os.path.dirname(__file__), "../../data/course_materials", file_name)
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    # Extract just the filename for cleaner database storage
    base_name = os.path.basename(file_path)
    
    # Ensure cloud connections are open before processing
    mongodb.connect()
    neo4j_db.connect()
    
    # Step 1: Slice the PDF
    chunks = process_pdf(file_path)
    
    print("Starting AI Analysis and Database Ingestion...")
    
    # We use chunks[:3] to only process the first 3 chunks during testing.
    # Once you confirm it works perfectly, remove the [:3] to process the entire textbook.
    for i, chunk in enumerate(chunks):
        print(f"\n ->Processing Chunk {i+1}/{len(chunks)}...")
        try:
            # Step 2: AI analysis and embedding
            vector, extraction = analyze_and_embed(chunk)
            # Step 3: Ingest into MongoDB and Neo4j
            ingest_to_databases(chunk, vector, extraction, base_name)
            
            # Rate Limit Protection: Pause for 4.5 seconds to stay under 15 RPM
            time.sleep(4.5)
            
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
            # If an error happens (like a brief network drop), wait 10 seconds before trying the next one
            time.sleep(10)
            continue
    
    print("Pipeline complete! Data is successfully stored in MongoDB and Neo4j.")
    
    # Close the graph database connection after processing to prevent memory leaks
    neo4j_db.close()

if __name__ == "__main__":
    # Run the pipeline with a sample PDF file located in the data/course_materials folder
    target_pdf = "C:/Users/1040G7/Documents/Documents/400lvl/Final Year project/adaptive-tutor-fyp/data/raw/Python_3_Object_Oriented_Programming.pdf"
    run_pipeline(target_pdf)
    