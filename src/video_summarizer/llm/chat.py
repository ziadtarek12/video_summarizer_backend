"""
Chat session management for video Q&A.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union

from video_summarizer.llm.client import get_llm_client, LLMClient


@dataclass
class ChatMessage:
    """A single message in the chat history."""
    role: str  # "user" or "assistant"
    content: str


@dataclass
class ChatSession:
    """
    Manages a chat session about video content.
    
    Maintains conversation history and provides context-aware responses
    using the video transcript.
    """
    
    transcript: str
    client: Optional[LLMClient] = None
    history: List[ChatMessage] = field(default_factory=list)
    max_history: int = 20  # Keep last N messages for context
    
    def __post_init__(self):
        if self.client is None:
            self.client = get_llm_client()
    
    def _build_context(self) -> str:
        """Build the full context including transcript and history."""
        # Build conversation history string
        history_str = ""
        if self.history:
            history_str = "\n\nPrevious conversation:\n"
            for msg in self.history[-self.max_history:]:
                role = "User" if msg.role == "user" else "Assistant"
                history_str += f"{role}: {msg.content}\n"
        
        return history_str
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt with transcript context."""
        return f"""You are a helpful assistant that answers questions about a video based on its transcript.

Here is the video transcript:
---
{self.transcript}
---

Instructions:
1. Answer questions based ONLY on the information in the transcript
2. If something is not covered in the transcript, say so
3. Be concise and helpful
4. Respond in the same language as the user's question
5. You can reference specific parts of the video by mentioning timestamps if available"""
    
    def chat(self, message: str) -> str:
        """
        Send a message and get a response.
        
        Args:
            message: The user's message.
        
        Returns:
            The assistant's response.
        """
        # Add user message to history
        self.history.append(ChatMessage(role="user", content=message))
        
        # Build prompt with context
        context = self._build_context()
        system_prompt = self._get_system_prompt()
        
        # Create user prompt with history context
        if len(self.history) > 1:
            user_prompt = f"{context}\n\nUser: {message}\n\nAssistant:"
        else:
            user_prompt = f"User question: {message}"
        
        # Get response
        response = self.client.complete(
            prompt=user_prompt,
            system=system_prompt,
        )
        
        # Add assistant response to history
        self.history.append(ChatMessage(role="assistant", content=response))
        
        return response
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.history = []
    
    def get_history(self) -> List[dict]:
        """Get the conversation history as a list of dicts."""
        return [{"role": msg.role, "content": msg.content} for msg in self.history]


def create_chat_session(
    transcript: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> ChatSession:
    """
    Create a new chat session for a video.
    
    Args:
        transcript: The video transcript text.
        provider: LLM provider ("google" or "openrouter").
        model: Specific model to use.
    
    Returns:
        Configured ChatSession.
    """
    client = get_llm_client(provider=provider, model=model)
    return ChatSession(transcript=transcript, client=client)
