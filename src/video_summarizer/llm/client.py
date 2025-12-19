"""
LLM client factory supporting multiple providers.
"""

import time
from typing import Optional, Protocol

from video_summarizer.config import LLMConfig, get_config


class LLMClientError(Exception):
    """Raised when LLM API calls fail."""
    pass


class LLMClient(Protocol):
    """Protocol for LLM clients."""
    
    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        """Send a completion request."""
        ...
    
    def complete_json(self, prompt: str, system: Optional[str] = None) -> dict:
        """Send a completion request expecting JSON response."""
        ...


class OpenRouterClient:
    """
    Client for OpenRouter API using OpenAI-compatible interface.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        config = get_config().llm
        
        self.api_key = api_key or config.openrouter_api_key
        self.model = model or config.openrouter_model
        self.base_url = base_url or config.openrouter_base_url
        self.max_tokens = max_tokens or config.max_tokens
        self.temperature = temperature or config.temperature
        
        self._client = None
    
    def _get_client(self):
        if self._client is not None:
            return self._client
        
        if not self.api_key:
            raise LLMClientError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable."
            )
        
        try:
            from openai import OpenAI
        except ImportError:
            raise LLMClientError(
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
        
        raise LLMClientError(f"API call failed after {max_retries} retries: {last_error}")
    
    def complete_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """
        Stream a completion request, yielding tokens as they arrive.
        
        Yields:
            str: Individual tokens/chunks of the response.
        """
        client = self._get_client()
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise LLMClientError(f"Streaming API call failed: {e}")
    
    def complete_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        import json
        import re
        
        response = self.complete(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        
        return _parse_json_response(response)


class GoogleAIClient:
    """
    Client for Google AI Studio (Gemini) API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        config = get_config().llm
        
        self.api_key = api_key or config.google_api_key
        self.model = model or config.google_model
        self.max_tokens = max_tokens or config.max_tokens
        self.temperature = temperature or config.temperature
        
        self._client = None
    
    def _get_client(self):
        if self._client is not None:
            return self._client
        
        if not self.api_key:
            raise LLMClientError(
                "Google API key is required. Set GOOGLE_API_KEY environment variable."
            )
        
        try:
            import google.generativeai as genai
        except ImportError:
            raise LLMClientError(
                "google-generativeai package is not installed. Install it with: pip install google-generativeai"
            )
        
        genai.configure(api_key=self.api_key)
        self._client = genai.GenerativeModel(self.model)
        
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
        import google.generativeai as genai
        
        client = self._get_client()
        
        # Combine system prompt with user prompt for Gemini
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"
        
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
        )
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = client.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                )
                
                return response.text
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
        
        raise LLMClientError(f"API call failed after {max_retries} retries: {last_error}")
    
    def complete_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """
        Stream a completion request, yielding tokens as they arrive.
        
        Yields:
            str: Individual tokens/chunks of the response.
        """
        import google.generativeai as genai
        
        client = self._get_client()
        
        # Combine system prompt with user prompt
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"
        
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
        )
        
        try:
            response = client.generate_content(
                full_prompt,
                generation_config=generation_config,
                stream=True,
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            raise LLMClientError(f"Streaming API call failed: {e}")
    
    def complete_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        response = self.complete(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        
        return _parse_json_response(response)


def _parse_json_response(response: str) -> dict:
    """Parse JSON from LLM response, handling various formats."""
    import json
    import re
    
    # Clean response - remove any leading/trailing whitespace
    response = response.strip()
    
    # Try direct parsing first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in markdown code blocks (with or without closing ```)
    # Handle case where response might be cut off
    json_patterns = [
        r'```json\s*\n([\s\S]*?)\n```',  # Complete code block with json
        r'```\s*\n([\s\S]*?)\n```',       # Complete code block without json
        r'```json\s*\n([\s\S]*)',         # Code block that might be cut off
        r'```\s*\n([\s\S]*)',             # Code block without json that might be cut off
    ]
    
    for pattern in json_patterns:
        json_match = re.search(pattern, response)
        if json_match:
            json_str = json_match.group(1).strip()
            # Remove trailing ``` if present
            json_str = re.sub(r'```\s*$', '', json_str).strip()
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix incomplete JSON by closing brackets
                fixed = _try_fix_incomplete_json(json_str)
                if fixed:
                    try:
                        return json.loads(fixed)
                    except json.JSONDecodeError:
                        pass
    
    # Try to find JSON object in the response
    obj_match = re.search(r'\{[\s\S]*\}', response)
    if obj_match:
        try:
            return json.loads(obj_match.group(0))
        except json.JSONDecodeError:
            # Try to fix incomplete JSON
            fixed = _try_fix_incomplete_json(obj_match.group(0))
            if fixed:
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    pass
    
    raise LLMClientError(f"Failed to parse JSON from response: {response[:500]}")


def _try_fix_incomplete_json(json_str: str) -> str:
    """Try to fix incomplete JSON by closing brackets and quotes."""
    # Count brackets and braces
    open_braces = json_str.count('{') - json_str.count('}')
    open_brackets = json_str.count('[') - json_str.count(']')
    
    # Check for unclosed strings (odd number of unescaped quotes after last complete value)
    # Simple heuristic: if ends with a letter/number without trailing quote or comma
    fixed = json_str.rstrip()
    
    # If string seems cut off mid-value, try to close it
    if fixed and fixed[-1] not in '",}]':
        # Check if we're in a string value
        if '"summary":' in fixed or '"key_points":' in fixed:
            # Find the last quote
            last_quote = fixed.rfind('"')
            last_colon = fixed.rfind(':')
            if last_colon > last_quote:
                # We're probably in an unquoted value, add closing quote
                fixed += '"'
            elif fixed.count('"') % 2 == 1:
                # Odd number of quotes, close the string
                fixed += '"'
    
    # Close array if in key_points
    if '"key_points"' in fixed and open_brackets > 0:
        fixed += ']' * open_brackets
    
    # Close braces
    if open_braces > 0:
        fixed += '}' * open_braces
    
    return fixed


def get_llm_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMClient:
    """
    Factory function to get the appropriate LLM client.
    
    Args:
        provider: "google" or "openrouter". Defaults to config value.
        api_key: Optional API key override.
        model: Optional model override.
    
    Returns:
        Configured LLM client.
    """
    config = get_config().llm
    provider = provider or config.provider
    
    if provider == "google":
        return GoogleAIClient(api_key=api_key, model=model)
    elif provider == "openrouter":
        return OpenRouterClient(api_key=api_key, model=model)
    else:
        raise LLMClientError(f"Unknown provider: {provider}. Use 'google' or 'openrouter'.")
