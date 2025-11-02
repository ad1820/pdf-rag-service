from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document 
from config.settings import OPENAI_API_KEY

embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

def create_faiss_index(text: str):
    if not text:
        raise ValueError("Cannot create index from empty text.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)
    
    if not chunks:
        raise ValueError("Text was too short to be split into chunks.")

    docs = [Document(page_content=chunk) for chunk in chunks]

    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore

def get_retriever(vectorstore):
    return vectorstore.as_retriever(search_kwargs={"k": 3})
