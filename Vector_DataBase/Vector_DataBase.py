from langchain_community.vectorstores import Chroma

# Create vector database and store embeddings
vector_db = Chroma.from_documents(
    documents=split_docs,          # chunked doc
    embedding=embedding_model,     # Ollama embedding model
    persist_directory="./chroma_db"  
)

vector_db.persist()

print("Vector database created successfully!")
