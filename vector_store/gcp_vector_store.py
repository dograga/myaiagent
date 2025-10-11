from typing import List, Optional
from google.cloud import aiplatform
from langchain.vectorstores import VectorStore
from langchain.embeddings.base import Embeddings
import numpy as np
import os

class GCPVectorStore(VectorStore):
    """GCP Vector Store implementation using Vertex AI Matching Engine."""
    
    def __init__(
        self,
        project_id: str,
        location: str,
        index_endpoint_name: str,
        deployed_index_id: str,
        embedding: Embeddings,
    ):
        """Initialize with necessary components."""
        self.project_id = project_id
        self.location = location
        self.index_endpoint_name = index_endpoint_name
        self.deployed_index_id = deployed_index_id
        self.embedding = embedding
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        # Get the index endpoint
        self.index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=index_endpoint_name
        )
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        **kwargs,
    ) -> List[str]:
        """Add texts to the vector store."""
        if metadatas is None:
            metadatas = [{} for _ in texts]
            
        # Generate embeddings
        embeddings = self.embedding.embed_documents(texts)
        
        # Convert to numpy array
        vectors = np.array(embeddings)
        
        # Upload to Vertex AI Matching Engine
        self.index_endpoint.upsert_datapoints(
            index_id=self.deployed_index_id,
            datapoints=[
                {
                    "datapoint_id": f"id_{i}",
                    "feature_vector": vector.tolist(),
                    "restricts": [
                        {"namespace": "text", "allow": [text]}
                    ]
                }
                for i, (vector, text) in enumerate(zip(vectors, texts))
            ]
        )
        
        return [f"id_{i}" for i in range(len(texts))]
    
    def similarity_search(
        self, query: str, k: int = 4, **kwargs
    ) -> List[dict]:
        """Return docs most similar to query."""
        # Get query embedding
        query_embedding = self.embedding.embed_query(query)
        
        # Query the index
        response = self.index_endpoint.find_neighbors(
            deployed_index_id=self.deployed_index_id,
            queries=[query_embedding],
            num_neighbors=k,
        )
        
        # Process and return results
        results = []
        for neighbor in response[0]:
            results.append({
                "text": neighbor.restricts[0]["allow"][0],
                "distance": neighbor.distance,
                "id": neighbor.id,
            })
            
        return results
    
    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        **kwargs,
    ) -> "GCPVectorStore":
        """Create a vector store from texts."""
        vector_store = cls(
            project_id=kwargs["project_id"],
            location=kwargs["location"],
            index_endpoint_name=kwargs["index_endpoint_name"],
            deployed_index_id=kwargs["deployed_index_id"],
            embedding=embedding,
        )
        vector_store.add_texts(texts, metadatas)
        return vector_store
