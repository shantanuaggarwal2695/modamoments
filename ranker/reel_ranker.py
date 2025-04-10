import os
import json
import logging
import numpy as np
from openai import OpenAI
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class ReelRanker:
    def __init__(self):
        """Initialize the ReelRanker with OpenAI client and configurations."""
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY environment variable not set! Functionality will be limited.")

        self.client = OpenAI(api_key=self.openai_api_key)
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.embedding_model = "text-embedding-3-small"
        self.llm_model = "gpt-4o"
        self.max_tokens = 8192
        self.embedding_dimensions = 1536  # Dimensions of the embedding vector

    def check_openai_connection(self) -> Dict[str, Any]:
        """
        Test the connection to OpenAI API.
        
        Returns:
            Dict: Status of the connection
        """
        if not self.openai_api_key:
            return {"connected": False, "error": "API key not configured"}

        try:
            # Try a simple completion to verify API connectivity
            self.client.embeddings.create(
                model=self.embedding_model,
                input="Connection test"
            )
            return {"connected": True}
        except Exception as e:
            logger.error(f"OpenAI connection failed: {str(e)}")
            return {"connected": False, "error": str(e)}

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a given text using OpenAI's embedding model.
        
        Args:
            text (str): The text to embed
            
        Returns:
            List[float]: The embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            # Return zeros vector as fallback
            return [0.0] * self.embedding_dimensions

    def prepare_conversation_context(self, query: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        Prepare a context string from the conversation history and current query.
        
        Args:
            query (str): Current user query
            conversation_history (List[Dict]): Previous messages in the conversation
            
        Returns:
            str: Formatted context string
        """
        # Format conversation history into a readable context
        context = ""

        # Add conversation history if present
        if conversation_history:
            for msg in conversation_history[-5:]:  # Only use last 5 messages for context
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context += f"{role}: {content}\n"

        # Add current query
        context += f"user: {query}"

        return context

    def extract_reel_features(self, reel: Dict[str, Any]) -> str:
        """
        Extract and format relevant features from a reel for embedding.
        
        Args:
            reel (Dict): Reel data including title, description, etc.
            
        Returns:
            str: Formatted reel features as text
        """
        features = []

        # Extract the most important features for ranking
        if "title" in reel and reel["title"]:
            features.append(f"Title: {reel['title']}")

        if "description" in reel and reel["description"]:
            features.append(f"Description: {reel['description']}")

        if "tags" in reel and reel["tags"]:
            features.append(f"Tags: {', '.join(reel['tags'])}")

        if "content" in reel and reel["content"]:
            # Truncate content if too long
            content = reel["content"]
            if len(content) > 500:
                content = content[:500] + "..."
            features.append(f"Content: {content}")

        # Add any other relevant features
        for key, value in reel.items():
            if key not in ["title", "description", "tags", "content", "id"] and value:
                if isinstance(value, list):
                    value = ", ".join(map(str, value))
                features.append(f"{key.capitalize()}: {value}")

        return "\n".join(features)

    def calculate_similarity(self, context_embedding: List[float], reel_embedding: List[float]) -> float:
        """
        Calculate cosine similarity between two embedding vectors.
        
        Args:
            context_embedding (List[float]): Embedding of the conversation context
            reel_embedding (List[float]): Embedding of the reel features
            
        Returns:
            float: Similarity score between 0 and 1
        """
        # Convert to numpy arrays for efficient calculation
        vec1 = np.array(context_embedding)
        vec2 = np.array(reel_embedding)

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Normalize to 0-1 range in case of floating-point issues
        return max(0.0, min(1.0, similarity))

    def analyze_relevance_with_llm(self, query: str, conversation_history: List[Dict[str, str]],
                                   top_reels: List[Dict[str, Any]], n: int = 3) -> List[Dict[str, Any]]:
        """
        Use OpenAI's LLM to analyze the relevance of top reels to the conversation.
        
        Args:
            query (str): Current user query
            conversation_history (List[Dict]): Previous messages
            top_reels (List[Dict]): Top reels based on embedding similarity
            n (int): Number of reels to analyze
            
        Returns:
            List[Dict]: Reels with adjusted relevance scores
        """
        try:
            # Take only the top N reels to analyze
            reels_to_analyze = top_reels[:n]

            # Format reels for the prompt
            reels_text = ""
            for i, reel in enumerate(reels_to_analyze):
                reel_features = self.extract_reel_features(reel)
                reels_text += f"REEL {i + 1}:\n{reel_features}\n\n"

            # Format conversation history
            conversation_text = self.prepare_conversation_context(query, conversation_history)

            # Create the prompt for the LLM
            prompt = f"""
            Analyze the relevance of each reel to the user's conversation.
            
            CONVERSATION:
            {conversation_text}
            
            REELS TO RANK:
            {reels_text}
            
            For each reel, provide:
            1. A relevance score from 0.0 to 1.0 (where 1.0 is most relevant)
            2. A brief explanation of why this score was assigned
            
            Respond with a JSON object in this format:
            {{
                "rankings": [
                    {{
                        "reel_index": 1,
                        "relevance_score": 0.85,
                        "explanation": "This reel is highly relevant because..."
                    }}
                ]
            }}
            """

            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=1000
            )

            # Parse the response
            response_content = response.choices[0].message.content
            result = json.loads(response_content)

            # Update the reels with the LLM-determined scores
            for ranking in result.get("rankings", []):
                reel_index = ranking.get("reel_index", 0) - 1  # Convert to 0-based index
                if 0 <= reel_index < len(reels_to_analyze):
                    reels_to_analyze[reel_index]["relevance_score"] = ranking.get("relevance_score", 0.5)
                    reels_to_analyze[reel_index]["explanation"] = ranking.get("explanation", "")

            # Sort the analyzed reels by their updated scores
            reels_to_analyze.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

            # Combine the analyzed reels with the remaining unanalyzed reels
            result_reels = reels_to_analyze + top_reels[n:]

            return result_reels

        except Exception as e:
            logger.error(f"Error in LLM relevance analysis: {str(e)}")
            # Fall back to original embedding-based ranking
            return top_reels

    def rank_reels(self, query: str, conversation_history: List[Dict[str, str]],
                   reels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank reels based on their relevance to the conversation.
        
        Args:
            query (str): Current user query
            conversation_history (List[Dict]): Previous messages in the conversation
            reels (List[Dict]): List of reels to rank
            
        Returns:
            List[Dict]: Ranked reels with relevance scores
        """
        # Prepare conversation context
        context = self.prepare_conversation_context(query, conversation_history)

        # Get embedding for the conversation context
        context_embedding = self.get_embedding(context)

        # Process each reel
        ranked_reels = []
        for reel in reels:
            try:
                # Extract features from the reel
                reel_features = self.extract_reel_features(reel)

                # Get embedding for the reel
                reel_embedding = self.get_embedding(reel_features)

                # Calculate similarity between context and reel
                similarity = self.calculate_similarity(context_embedding, reel_embedding)

                # Create a copy of the reel with similarity score
                ranked_reel = reel.copy()
                ranked_reel["relevance_score"] = similarity

                ranked_reels.append(ranked_reel)

            except Exception as e:
                logger.error(f"Error processing reel {reel.get('id', 'unknown')}: {str(e)}")
                # Add the reel with a low relevance score
                reel_copy = reel.copy()
                reel_copy["relevance_score"] = 0.0
                reel_copy["error"] = str(e)
                ranked_reels.append(reel_copy)

        # Sort reels by relevance score (highest first)
        ranked_reels.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # Use LLM to further analyze the top reels if there are enough reels
        if len(ranked_reels) >= 3:
            ranked_reels = self.analyze_relevance_with_llm(query, conversation_history, ranked_reels)

        return ranked_reels
