from google import genai
from google.genai import types
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Gemini client
client = None


def get_gemini_client():
    """
    Get or initialize Gemini client
    """
    global client
    if client is None:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            logger.info("✅ Gemini client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini client: {e}")
            raise
    return client


def generate_text(prompt: str, model_name: str = "gemini-2.5-flash-lite") -> str:
    """
    Generate text using Gemini
    
    Args:
        prompt: Input prompt
        model_name: Model to use
        
    Returns:
        Generated text
    """
    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text
    except Exception as e:
        logger.error(f"❌ Failed to generate text: {e}")
        raise


def generate_embedding(text: str) -> list:
    """
    Generate embeddings using Gemini
    
    Args:
        text: Input text to embed
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        client = get_gemini_client()
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        # Extract the embedding values from the response
        return result.embeddings[0].values
    except Exception as e:
        logger.error(f"❌ Failed to generate embedding: {e}")
        raise


def generate_text_with_config(
    prompt: str, 
    model_name: str = "gemini-2.0-flash-exp",
    temperature: float = 0.7,
    max_output_tokens: int = 2048
) -> str:
    """
    Generate text with custom configuration
    
    Args:
        prompt: Input prompt
        model_name: Model to use
        temperature: Controls randomness (0.0-2.0)
        max_output_tokens: Maximum tokens in response
        
    Returns:
        Generated text
    """
    try:
        client = get_gemini_client()
        
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        return response.text
    except Exception as e:
        logger.error(f"❌ Failed to generate text with config: {e}")
        raise
