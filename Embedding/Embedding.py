from langchain_community.embeddings import OllamaEmbeddings

embedding_model = OllamaEmbeddings(
    model="nomic-embed-text"  
)

embeddings = embedding_model.embed_documents(
    [doc.page_content for doc in split_docs]
)

print("First embedding vector:")
print(embeddings[0])