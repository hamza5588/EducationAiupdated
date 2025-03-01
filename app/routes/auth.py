from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify
from app.models import UserModel
import logging
import requests

logger = logging.getLogger(__name__)
bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            user_id = UserModel.create_user(
                username=request.form['username'],
                useremail=request.form['useremail'],
                password=request.form['password'],
                class_standard=request.form['class_standard'],
                medium=request.form['medium'],
                groq_api_key=request.form['groq_api_key']
            )
            return redirect(url_for('auth.login'))
        except ValueError as e:
            return render_template('register.html', error=str(e))
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return render_template('register.html', error="Registration failed")
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            user = UserModel.get_user_by_email(request.form['useremail'])
            if user and user['password'] == request.form['password']:
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['groq_api_key'] = user['groq_api_key']
                session.permanent = True
                return redirect(url_for('chat.index'))
            return render_template('login.html', error="Invalid credentials")
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return render_template('login.html', error="Login failed")
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@bp.route('/check_session')
def check_session():
    if 'user_id' in session:
        return {'logged_in': True, 'username': session.get('username')}
    return {'logged_in': False}, 401

@bp.route('/session', methods=['GET'])
def get_session():
    """Get OpenAI realtime session token"""
    try:
        api_key = "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"
        if not api_key:
            return jsonify({
                'error': 'OpenAI API key not found in session'
            }), 401

        url = "https://api.openai.com/v1/realtime/sessions"
        
        payload = {
            "model": "gpt-4o-realtime-preview-2024-12-17",
            "modalities": ["audio", "text"],
            "instructions": """Role: You are Mr. Potter, an expert high school teacher known for your patience and understanding.

            Teaching Approach:

            Begin your first interaction with a student by saying: "Hello, my name is Mr. Potter."
            Ask, "Can I have your name?" and remember it for future interactions.
            Once the student’s name is known, greet them directly in future interactions: "[Student's name], how can I help you today?"
            Break down problems into simpler components to identify gaps in understanding.
            Provide tailored explanations based on student responses.
            Verify understanding by offering practice problems.
            Let students choose whether to check their understanding or tackle more challenges.
            Adjust problem difficulty based on student progress.
            Additional Guidelines:

            Always maintain patience, provide encouragement, and ensure complete understanding before moving to more complex topics.
            Match questions to appropriate grade levels.
            If a student asks about the source of your knowledge, explain: "My information comes from data crawled from the internet, allowing me to access a wide range of educational resources and stay current with academic content."""
        }
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            return jsonify({
                'error': 'Failed to get session token'
            }), response.status_code

        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error getting session token: {str(e)}")
        return jsonify({'error': 'Network error occurred'}), 500
    except Exception as e:
        logger.error(f"Error getting session token: {str(e)}")
        return jsonify({'error': str(e)}), 500