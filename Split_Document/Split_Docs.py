from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      
    chunk_overlap=100    
)

split_docs = text_splitter.split_documents(documents)

for i, doc in enumerate(split_docs):
    print(f"\n--- Chunk {i+1} ---")
    print(doc.page_content)