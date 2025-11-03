"""
Chat routes
"""

from flask import Blueprint, request, jsonify
from database import db_session
from services import db_operations, perplexity, openai_service
from routes.auth import get_current_user
from config import Config
import threading
from datetime import datetime, timezone
from utils.datetime_utils import now_utc

bp = Blueprint('chat', __name__)


@bp.route('/send', methods=['POST'])
def send_message():
    """Send message and get AI response with patient memory"""
    import time
    start_time = time.time()
    
    user = get_current_user()
    data = request.get_json()
    
    conversation_id = data.get('conversationId')  # Optional for temporary chats
    message = data.get('message')
    model = data.get('model', 'sonar-pro')  # Default to sonar-pro for better quality
    
    if not message:
        return jsonify({'error': 'message is required'}), 400
    
    # Temporary chat mode - no conversation ID provided
    is_temporary_chat = not conversation_id
    
    db = db_session()
    try:
        # Load conversation context
        if not is_temporary_chat:
            # Get last 10 messages for context
            from sqlalchemy import desc
            from models import Message
            history = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(desc(Message.created_at)).limit(10).all()
            history = list(reversed(history))
            
            session_context = perplexity.build_session_context([
                {'role': str(msg.role), 'content': str(msg.content)}
                for msg in history
            ], max_messages=10)
        else:
            # Temporary chat - no history, just the current message
            session_context = []
        
        # Load user preferences AND patient memory
        user_context = None
        patient_memory_context = []
        
        if user:
            preferences_data = db_operations.get_user_preferences(db, str(user.id))
            
            if preferences_data:
                user_context = {
                    'preferences': {
                        'ageGroup': str(preferences_data.age_group) if preferences_data.age_group is not None else None,
                        'responseStyle': str(preferences_data.response_style) if preferences_data.response_style is not None else None,
                        'languageComplexity': str(preferences_data.language_complexity) if preferences_data.language_complexity is not None else None,
                        'includeMedicalTerms': preferences_data.include_medical_terms if preferences_data.include_medical_terms is not None else None,
                        'responseLength': str(preferences_data.response_length) if preferences_data.response_length is not None else None
                    }
                }
            
            # Load patient memory for personalized responses
            from models import PatientMemory
            patient_memories = db.query(PatientMemory).filter(
                PatientMemory.user_id == str(user.id)
            ).limit(20).all()
            
            if patient_memories:
                memory_entries = []
                for pm in patient_memories:
                    entry = f"{pm.entity_type}: {pm.entity_name}"
                    if pm.relationships is not None:
                        entry += f" ({pm.relationships})"
                    memory_entries.append(entry)
                
                patient_memory_context = memory_entries
        
        # Build messages for Perplexity with patient memory
        messages_for_api = session_context.copy()
        new_user_message = {'role': 'user', 'content': message}
        
        last_msg = messages_for_api[-1] if messages_for_api else None
        if last_msg and last_msg['role'] == 'user':
            last_msg['content'] += f"\n{new_user_message['content']}"
        else:
            messages_for_api.append(new_user_message)
        
        print(f"[PERF] DB operations: {time.time() - start_time:.2f}s")
        api_start = time.time()
        
        # Call LLM API based on provider configuration
        if Config.LLM_PROVIDER == 'openai':
            response = openai_service.call_openai(
                messages_for_api,
                model if model.startswith('gpt') else 'gpt-4o',  # Use OpenAI model if gpt- prefix, else use default
                user_context,
                message,
                patient_memory_context if patient_memory_context else None
            )
        else:  # Default to Perplexity
            response = perplexity.call_perplexity(
                messages_for_api,
                model,
                user_context,
                message,
                patient_memory_context if patient_memory_context else None
            )
        
        print(f"[PERF] LLM API ({Config.LLM_PROVIDER}): {time.time() - api_start:.2f}s")
        
        # Save messages with embeddings enabled
        if not is_temporary_chat:
            # Save in background thread for faster response
            def save_messages_and_extract_memory():
                bg_db = db_session()
                try:
                    # Save user message WITH embedding
                    db_operations.create_message(bg_db, conversation_id, 'user', message, generate_embedding=True)
                    
                    # Save assistant message WITH embedding
                    assistant_msg = db_operations.create_message(
                        bg_db,
                        conversation_id,
                        'assistant',
                        response['content'],
                        response.get('citations'),
                        response.get('searchResults'),
                        response.get('model'),
                        generate_embedding=True
                    )
                    
                    # Extract patient memory from conversation
                    if user:
                        db_operations.extract_and_save_patient_memory(
                            bg_db,
                            str(user.id),
                            conversation_id,
                            message,
                            response['content']
                        )
                    
                    print("[PERF] Background save and memory extraction completed")
                except Exception as e:
                    print(f"[PERF] Background save failed: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    bg_db.close()
            
            # Start background save
            threading.Thread(target=save_messages_and_extract_memory, daemon=True).start()
            
            print(f"[PERF] ✅ Total response time: {time.time() - start_time:.2f}s")
            
            # Return response immediately
            return jsonify({
                'message': {
                    'id': f'msg_{int(now_utc().timestamp() * 1000)}',
                    'conversationId': conversation_id,
                    'role': 'assistant',
                    'content': response['content'],
                    'citations': response.get('citations'),
                    'searchResults': response.get('searchResults'),
                    'model': response.get('model'),
                    'createdAt': now_utc().isoformat()
                },
                'citations': response.get('citations'),
                'searchResults': response.get('searchResults')
            }), 200
        else:
            print(f"[PERF] ✅ Total response time: {time.time() - start_time:.2f}s")
            # Return response for temporary chat (no database storage)
            return jsonify({
                'message': {
                    'id': f'temp_{int(now_utc().timestamp() * 1000)}',
                    'conversationId': None,
                    'role': 'assistant',
                    'content': response['content'],
                    'citations': response.get('citations'),
                    'searchResults': response.get('searchResults'),
                    'model': response.get('model'),
                    'createdAt': now_utc().isoformat()
                },
                'citations': response.get('citations'),
                'searchResults': response.get('searchResults')
            }), 200
        
    except Exception as error:
        print(f"Chat send failed: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(error)}), 500
    finally:
        db.close()


@bp.route('/models', methods=['GET'])
def get_models():
    """Get available models for configured LLM provider"""
    if Config.LLM_PROVIDER == 'openai':
        return jsonify({
            "provider": "openai",
            "models": openai_service.AVAILABLE_MODELS
        }), 200
    else:
        return jsonify({
            "provider": "perplexity",
            "models": perplexity.AVAILABLE_MODELS
        }), 200
    return jsonify(perplexity.AVAILABLE_MODELS), 200
