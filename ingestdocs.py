"""
Ingestion of documentation files.
"""
from langchain.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

import os
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

def ingest_docs(name: str, docsurl: str, storepath: str, forced: bool = False) -> None:
    """
    Embeds documentations into a vectorstore using embeddings.

    Args:
        docsurl (str): link to the documentation page.
        storepath (str): Path to the vectorstore.
    """
    # checking if docs aleady exists.
    try:
        with open('stored_docs.json', 'r') as f:
            stored_docs = json.load(f)
            if name.lower() in stored_docs.keys():
                print(f"Documentations of {name.lower()} already exists")
                if not forced:
                    return stored_docs.get(name.lower())
                else:
                    print(f"recollecting {name.lower()} with the given url")
            
        with open('stored_docs.json', 'w') as f:
            entry = {
                name.lower(): storepath
            }
            stored_docs.update(entry)
            json.dump(stored_docs, f)
            print(f"created new entry for {name.lower()}")
            
    except FileNotFoundError:
        with open('stored_docs.json', 'w') as f:
            entry = {
                name.lower(): storepath
            }
            json.dump(entry, f)
            print(f"created new entry for {name.lower()}")

    # getting urls.
    response = requests.get(docsurl)
    if response.status_code == 200:
        content = response.text
    else:
        raise ValueError('Incorrect link provided.')

    soup = BeautifulSoup(content, "lxml")
    if ".html" in docsurl:
        docsurl = "/".join(docsurl.split('/')[:-1])

    links = list(dict.fromkeys([urljoin(docsurl, a_tag['href'].split('#')[0]) for a_tag in soup.find_all('a', href=True)]))
    
    # loading
    print("loading documentations...")
    documents = UnstructuredURLLoader(links).load()
    
    # creating chunks
    print("chunking documentations...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)
    docs = splitter.split_documents(documents=documents)
    
    # embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
    )
    # vectorstore
    print(f"building vectorstore")
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(storepath)

    print(f"vectorstore for {name.lower()} is ready!")
    return storepath


# store_path = ingest_docs('langchain', 'https://api.python.langchain.com/en/stable/api_reference.html', 'docstore/langchain')
# print(store_path)

# store_path = ingest_docs('django', 'https://django.readthedocs.io/en/stable/', 'docstore/django')
# print(store_path)