from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("your_document.pdf")

documents = loader.load()

for i, doc in enumerate(documents):
    print(f"\n--- Page {i+1} ---")
    print(doc.page_content)
    