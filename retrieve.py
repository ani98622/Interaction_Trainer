from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import FlashrankRerank
from langchain_chroma import Chroma

def create_compressed_retriever(pdf_paths):
    documents = []
    for path in pdf_paths:
        loader = PyPDFLoader(path)
        documents.extend(loader.load())
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    model_name = "sentence-transformers/all-mpnet-base-v2"
    model_kwargs = {'device': 'cpu'}
    embedding = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs
    )
    retriever = Chroma.from_documents(texts, embedding).as_retriever(search_kwargs={"k": 20})
    compressor = FlashrankRerank()
    compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)
    return compression_retriever

pdf_proj_1 = ["./data/FAQ_SWAYAM 1.pdf"]
pdf_proj_3 = ["./data/transformer.pdf"]

compressed_retriever1 = create_compressed_retriever(pdf_proj_1)
compressed_retriever2 = create_compressed_retriever(pdf_proj_3)
