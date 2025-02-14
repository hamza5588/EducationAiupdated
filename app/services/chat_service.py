# app/services/chat_service.py
from typing import List, Dict, Optional, Any
from app.models import ChatModel, ConversationModel, VectorStoreModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatService:
    """Service class for handling chat-related business logic"""
    
    def __init__(self, user_id: int, api_key: str):
        self.user_id = user_id
        self.chat_model = ChatModel(api_key)
        self.conversation_model = ConversationModel(user_id)
        self.vector_store = VectorStoreModel()
        
    def format_chat_history(self, history: List[Dict]) -> List[Dict]:
        """Format chat history for the LLM"""
        formatted_history = []
        for msg in history:
            # Map 'bot' role to 'assistant' and ensure we access the correct message field
            role = 'assistant' if msg.get('role') == 'bot' else msg.get('role', 'user')
            content = msg.get('message', '')  # Get message content with default empty string
            
            if content and role:  # Only add if we have both content and role
                formatted_history.append({
                    'role': role,
                    'content': content
                })
        return formatted_history
        
    def process_message(self, message: str, 
                       conversation_id: Optional[int] = None,
                       system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Process a user message and generate a response"""
        try:
            # Create new conversation if needed
            if not conversation_id:
                conversation_id = self.conversation_model.create_conversation(
                    title=message[:50]
                )
            
            # Save user message
            self.conversation_model.save_message(
                conversation_id=conversation_id,
                message=message,
                role='user'
            )
            
            # Get relevant context from vector store
            context = ""
            try:
                if self.vector_store._vectorstore:
                    relevant_docs = self.vector_store.search_similar(message, k=3)
                    if relevant_docs:
                        context = "Using the provided documents, I found this relevant information:\n\n" + "\n".join(
                            [f"• {doc.page_content.strip()}" for doc in relevant_docs]
                        )
                        logger.info("Found relevant context from documents")
            except Exception as e:
                logger.warning(f"Error retrieving context: {str(e)}")
            
            # Enhance system prompt with context
            enhanced_prompt = "You are a helpful assistant. "
            if system_prompt:
                enhanced_prompt += system_prompt
            if context:
                enhanced_prompt += f"\n\n{context}\n\nPlease use this information to answer the question accurately."
            
            # Get and format chat history
            raw_history = self.conversation_model.get_chat_history(conversation_id)
            formatted_history = self.format_chat_history(raw_history)
            
            # For debugging
            logger.debug(f"Formatted history: {formatted_history}")
            
            # Generate response
            response = self.chat_model.generate_response(
                input_text=message,
                system_prompt=enhanced_prompt,
                chat_history=formatted_history
            )
            
            # Save bot response
            self.conversation_model.save_message(
                conversation_id=conversation_id,
                message=response,
                role='bot'
            )
            
            return {
                'response': response,
                'conversation_id': conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    def get_recent_conversations(self, limit: int = 4) -> List[Dict[str, Any]]:
        """Get user's recent conversations"""
        try:
            return self.conversation_model.get_conversations(limit=limit)
        except Exception as e:
            logger.error(f"Error retrieving conversations: {str(e)}")
            raise

    def get_conversation_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Get messages for a specific conversation"""
        try:
            raw_messages = self.conversation_model.get_chat_history(conversation_id)
            return [
                {
                    'role': msg.get('role', 'user'),
                    'message': msg.get('message', ''),
                    'created_at': msg.get('created_at', datetime.now().isoformat())
                }
                for msg in raw_messages
            ]
        except Exception as e:
            logger.error(f"Error retrieving messages: {str(e)}")
            raise

    def create_conversation(self, title: str) -> int:
        """Create a new conversation"""
        try:
            return self.conversation_model.create_conversation(title)
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise

    def delete_conversation(self, conversation_id: int) -> None:
        """Delete a conversation"""
        try:
            self.conversation_model.delete_conversation(conversation_id)
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            raise

    def clean_old_conversations(self, max_conversations: int = 50) -> None:
        """Clean up old conversations beyond the maximum limit"""
        try:
            conversations = self.conversation_model.get_conversations()
            if len(conversations) > max_conversations:
                for conv in conversations[max_conversations:]:
                    self.delete_conversation(conv['id'])
        except Exception as e:
            logger.error(f"Error cleaning old conversations: {str(e)}")
            raise