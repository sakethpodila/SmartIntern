import faiss
import numpy as np
from agents.embed import get_embeddings
from langchain.schema import Document
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS


class VectorDatabase:
    def __init__(self):
        self.vector_store = None  # This will hold the FAISS index

    def create_vector_store(self, chunks: list[str], metadatas:list[dict]):
        """Creates and stores the FAISS vector database"""
        
        print(f"Inside create_vector_store: {len(chunks)} chunks", flush=True)
        print(chunks)
        embeddings = get_embeddings(chunks)
        dimension = len(embeddings[0])
        
        print(len(embeddings), flush=True)
        # Create FAISS index
        faiss_index = faiss.IndexFlatL2(dimension)
        faiss_index.add(np.array(embeddings, dtype=np.float32))

        # Create a document store
        documents_dict = {
            str(i): Document(page_content=chunks[i], metadata=metadatas[i])
            for i in range(len(chunks))
        }
        docstore = InMemoryDocstore(documents_dict)

        index_to_docstore_id = {i: str(i) for i in range(len(chunks))}

        # Store in global object
        self.vector_store = FAISS(
            index=faiss_index,
            docstore=docstore,
            index_to_docstore_id=index_to_docstore_id,
            embedding_function=get_embeddings,
        )