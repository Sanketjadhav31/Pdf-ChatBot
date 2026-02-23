for chunk in split_docs:
    source = chunk.metadata.get("source")
    page = chunk.metadata.get("page")
    current_page_id = f"{source}:{page}"

    print("Source:", source)
    print("Page:", page)
    print("ID:", current_page_id)
    print("-" * 40)