# app/routes/chat.py
from flask import Blueprint, redirect, request, session, jsonify, render_template, url_for
from app.services import ChatService, PromptService
from app.utils.decorators import login_required
import logging
import requests
import os
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)
bp = Blueprint('chat', __name__)

@bp.route('/')
@login_required
def index():
    """Render the main chat interface"""
    return render_template('chat.html')

# Add these routes to chat.py

from app.services import PromptService

@bp.route('/get_prompt')
def get_prompt():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    try:
        prompt_service = PromptService(session['user_id'])
        current_prompt = prompt_service.get_prompt()
        return jsonify({'prompt': current_prompt})
    except Exception as e:
        logger.error(f"Error retrieving prompt: {str(e)}")
        return jsonify({'error': 'Failed to retrieve prompt'}), 500

@bp.route('/update_prompt', methods=['POST'])
def update_prompt():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    try:
        data = request.json
        new_prompt = data.get('prompt')
   
        
        if not new_prompt:
            return jsonify({'error': 'Prompt is required'}), 400
            
        prompt_service = PromptService(session['user_id'])
        prompt_service.update_prompt(new_prompt)
        
        return jsonify({
            'success': True,
            'message': 'Prompt updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating prompt: {str(e)}")
        return jsonify({'error': 'Failed to update prompt'}), 500

@bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat messages and generate responses"""
    try:
        data = request.json
        user_input = data.get('input', '').strip()
        conversation_id = data.get('conversation_id')

        if not user_input:
            return jsonify({'error': 'Empty message'}), 400

        # Initialize services
        chat_service = ChatService(session['user_id'], session['groq_api_key'])
        prompt_service = PromptService(session['user_id'])

        # Get system prompt
        system_prompt = prompt_service.get_prompt()

        # Process message and generate response
        try:
            result = chat_service.process_message(
                message=user_input,
                conversation_id=conversation_id,
                system_prompt=system_prompt
            )
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return jsonify({
                'error': 'Failed to generate response. Please check your API key.'
            }), 500

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@bp.route('/create_conversation', methods=['POST'])
@login_required
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.json
        title = data.get('title', 'New Conversation')
        
        chat_service = ChatService(session['user_id'], session['groq_api_key'])
        conversation_id = chat_service.create_conversation(title)
        
        return jsonify({
            'conversation_id': conversation_id,
            'title': title
        })
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        return jsonify({'error': 'Failed to create conversation'}), 500

@bp.route('/get_conversations')
@login_required
def get_conversations():
    """Get user's recent conversations"""
    try:
        chat_service = ChatService(session['user_id'], session['groq_api_key'])
        conversations = chat_service.get_recent_conversations()
        return jsonify(conversations)
    except Exception as e:
        logger.error(f"Error retrieving conversations: {str(e)}")
        return jsonify({'error': 'Failed to retrieve conversations'}), 500

@bp.route('/get_messages/<int:conversation_id>')
@login_required
def get_messages(conversation_id):
    """Get messages for a specific conversation"""
    try:
        chat_service = ChatService(session['user_id'], session['groq_api_key'])
        messages = chat_service.get_conversation_messages(conversation_id)
        return jsonify(messages)
    except Exception as e:
        logger.error(f"Error retrieving messages: {str(e)}")
        return jsonify({'error': 'Failed to retrieve messages'}), 500

@bp.route('/delete_conversation/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        chat_service = ChatService(session['user_id'], session['groq_api_key'])
        chat_service.delete_conversation(conversation_id)
        return jsonify({'message': 'Conversation deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        return jsonify({'error': 'Failed to delete conversation'}), 500

@bp.route('/session', methods=['GET'])
@login_required
def get_session():
    try:
        url = "https://api.openai.com/v1/realtime/sessions"
        
        # Get API key from session instead of env
        api_key = "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"
        if not api_key:
            return jsonify({'error': 'API key not found. Please update your API key.'}), 401
        
        payload = {
            "model": "gpt-4o-realtime-preview-2024-12-17",
            "modalities": ["audio", "text"],
            "instructions": """Role:
            You are Mr. Potter, an expert high school teacher known for your patience and understanding.

            Teaching Approach:

            Begin every interaction with:
            "Hello, my name is Mr. Potter."
            Ask:
            "Can I have your name?" (Remember the student's name for future interactions.)
            Once the student provides a name, respond with:
            "[Student's name], how can I help you today?"
            Break down problems into simpler components to identify gaps in understanding.
            Provide tailored explanations based on the student’s responses.
            Verify understanding by offering practice problems.
            Let the student choose to check their understanding or tackle more challenges.
            Adjust problem difficulty based on student progress.
            Additional Notes:

            Do not ask for the student's name again once they have provided it.
            If a student asks about the source of your knowledge, explain that your information comes from data crawled from the internet, which allows you to access a wide range of educational resources and stay current with academic content.
            Always maintain patience, provide encouragement, and ensure complete understanding before moving on to more complex topics.
            Match questions to the appropriate grade level of the student."""
                    }
        
        headers = {
            'Authorization': f'Bearer {api_key}',  # Use session API key
            'Content-Type': 'application/json'
        }

        logger.info("Making request to OpenAI API")
        response = requests.post(url, json=payload, headers=headers)
        
        if not response.ok:
            error_message = f"OpenAI API error: {response.text}"
            logger.error(error_message)
            return jsonify({'error': error_message}), response.status_code

        response_data = response.json()
        logger.info("Successfully created OpenAI session")
        return jsonify(response_data)

    except Exception as e:
        error_message = f"Error creating session: {str(e)}"
        logger.error(error_message)
        return jsonify({'error': error_message}), 500
