"""
OpenRouter API client using OpenAI-compatible interface.
"""

import time
from typing import Optional

from video_summarizer.config import LLMConfig, get_config


class OpenRouterError(Exception):
    """Raised when OpenRouter API calls fail."""
    pass


class OpenRouterClient:
    """
    Client for OpenRouter API using OpenAI-compatible interface.
    
    OpenRouter provides access to various LLMs through a unified API
    that's compatible with the OpenAI client library.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key. Defaults to config value.
            model: Model to use. Defaults to config value.
            base_url: API base URL. Defaults to OpenRouter's URL.
            max_tokens: Maximum tokens in response. Defaults to config value.
            temperature: Sampling temperature. Defaults to config value.
        """
        config = get_config().llm
        
        self.api_key = api_key or config.api_key
        self.model = model or config.model
        self.base_url = base_url or config.base_url
        self.max_tokens = max_tokens or config.max_tokens
        self.temperature = temperature or config.temperature
        
        self._client = None
    
    def _get_client(self):
        """Lazy load the OpenAI client."""
        if self._client is not None:
            return self._client
        
        if not self.api_key:
            raise OpenRouterError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable."
            )
        
        try:
            from openai import OpenAI
        except ImportError:
            raise OpenRouterError(
                "openai package is not installed. Install it with: pip install openai"
            )
        
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        return self._client
    
    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> str:
        """
        Send a completion request to OpenRouter.
        
        Args:
            prompt: The user prompt.
            system: Optional system prompt.
            max_tokens: Override default max tokens.
            temperature: Override default temperature.
            max_retries: Number of retries on failure.
            retry_delay: Delay between retries in seconds.
        
        Returns:
            The model's response text.
        
        Raises:
            OpenRouterError: If the API call fails after retries.
        """
        client = self._get_client()
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens or self.max_tokens,
                    temperature=temperature or self.temperature,
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
        
        raise OpenRouterError(f"API call failed after {max_retries} retries: {last_error}")
    
    def complete_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """
        Send a completion request expecting JSON response.
        
        Args:
            prompt: The user prompt (should ask for JSON).
            system: Optional system prompt.
            max_tokens: Override default max tokens.
        
        Returns:
            Parsed JSON response as a dictionary.
        
        Raises:
            OpenRouterError: If the API call fails or JSON parsing fails.
        """
        import json
        
        response = self.complete(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temperature for structured output
        )
        
        # Try to extract JSON from the response
        try:
            # First, try direct parsing
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in markdown code blocks
        import re
        json_match = re.search(r'```(?:json)?\s*\n([\s\S]*?)\n```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object/array in the response
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        raise OpenRouterError(f"Failed to parse JSON from response: {response[:500]}")
