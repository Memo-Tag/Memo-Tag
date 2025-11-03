"""
Authentication routes
Replicates server/_core/oauth.ts functionality
"""

from flask import Blueprint, request, jsonify, make_response
from functools import wraps
from typing import Optional
from database import db_session
from services import db_operations
from utils.auth import create_session_token, verify_session, hash_password, verify_password, generate_id
from config import Config
from models import User, Conversation, PatientMemory, UserPreferences, UserLoginHistory, Message
from sqlalchemy import update, delete
import jwt
import requests

bp = Blueprint('auth', __name__)


# Authentication decorator
def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Please login (10001)'}), 401
        return f(user=user, *args, **kwargs)
    return decorated_function


def get_current_user():
    """Get current user from session cookie"""
    token = request.cookies.get(Config.COOKIE_NAME)
    if not token:
        return None
    
    session = verify_session(token)
    if not session:
        return None
    
    user_id = session.get('openId')
    if not user_id:
        return None
    
    db = db_session()
    user = db_operations.get_user(db, user_id)
    db.close()
    
    return user


@bp.route('/me', methods=['GET'])
def get_me():
    """Get current user and all active login sessions"""
    user = get_current_user()
    if not user:
        return jsonify(None), 200
    
    user_id = str(user.id)
    
    # Get ALL active login sessions across all users
    db = db_session()
    try:
        active_logins = db_operations.get_all_active_logins(db)
        
        login_history = [{
            'id': login.id,
            'userId': login.user_id,
            'email': login.email,
            'name': login.name,
            'loginMethod': login.login_method,
            'profileImage': login.profile_image,
            'action': login.action,
            'timestamp': login.timestamp.isoformat() if login.timestamp is not None else None,
            'isActive': login.is_active,
            'ipAddress': login.ip_address,
            'userAgent': login.user_agent
        } for login in active_logins]
        
        return jsonify({
            'currentUser': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'loginMethod': user.login_method,
                'profileImage': user.profile_image,
                'lastSignedIn': user.last_signed_in.isoformat() if user.last_signed_in is not None else None
            },
            'activeLogins': login_history,
            'totalActiveSessions': len(login_history)
        }), 200
    finally:
        db.close()


@bp.route('/register', methods=['POST'])
def register():
    """Register new user with email/password"""
    try:
        try:
            # Try to parse JSON - accept both form-data and raw JSON
            data = request.get_json(force=True, silent=False)
        except Exception as json_error:
            # If JSON parsing fails, provide helpful error
            error_msg = str(json_error)
            if "Expecting value" in error_msg:
                return jsonify({
                    'error': 'Invalid JSON format. Special characters like @, !, #, $ must be escaped. Use passwords without special characters for simplicity.'
                }), 400
            print(f"JSON parse error: {json_error}")
            return jsonify({'error': f'Invalid JSON format: {str(json_error)}'}), 400
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        name = data.get('name', '').strip()
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        db = db_session()
        
        try:
            # Check if email already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                db.close()
                return jsonify({'error': 'Email already registered. Please login or use a different email.'}), 400
            
            # Clean up old login history for this email (from deleted accounts)
            # This happens when a user was deleted from Supabase but login history remains
            db.execute(delete(UserLoginHistory).where(UserLoginHistory.email == email))
            db.commit()
            
            # Generate IDs and hash password BEFORE any DB operations
            user_id = generate_id('user')
            password_hash_value = hash_password(password)
            
            # Create user
            new_user = User(
                id=user_id,
                name=name if name else email.split('@')[0],
                email=email,
                password_hash=password_hash_value,
                login_method='local',
                role='user'
            )
            db.add(new_user)
            db.flush()  # Flush user to DB
            
            # Record login history
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            db_operations.record_login_history(
                db,
                user_id=user_id,
                email=email,
                name=name if name else email.split('@')[0],
                login_method='local',
                action='signup',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Transfer guest data if exists (without internal commit)
            try:
                token = request.cookies.get(Config.COOKIE_NAME)
                if token:
                    session = verify_session(token)
                    if session:
                        guest_id = session.get('openId')
                        if guest_id and guest_id.startswith('guest_'):
                            # Inline transfer to avoid nested commits
                            db.execute(
                                update(Conversation)
                                .where(Conversation.user_id == guest_id)
                                .values(user_id=user_id, is_guest=False)
                            )
                            db.execute(
                                update(PatientMemory)
                                .where(PatientMemory.user_id == guest_id)
                                .values(user_id=user_id)
                            )
                            existing_prefs = db.query(UserPreferences).filter(
                                UserPreferences.user_id == user_id
                            ).first()
                            if not existing_prefs:
                                db.execute(
                                    update(UserPreferences)
                                    .where(UserPreferences.user_id == guest_id)
                                    .values(user_id=user_id)
                                )
            except Exception as e:
                print(f"Warning: Failed to transfer guest data: {e}")
                # Don't fail registration
            
            # Final commit - ALL operations in one transaction
            db.commit()
            
            # Create session token AFTER commit
            session_token = create_session_token(
                user_id,
                name if name else email.split('@')[0],
                Config.ONE_YEAR_MS
            )
            
            # Return response with cookie
            response = make_response(jsonify({
                'id': user_id,
                'email': email
            }), 201)
            
            response.set_cookie(
                Config.COOKIE_NAME,
                session_token,
                max_age=Config.ONE_YEAR_SECONDS,
                httponly=True,
                secure=False,
                samesite='Lax',
                path='/',
                domain=None
            )
            
            return response
            
        except Exception as error:
            db.rollback()
            print(f"Register error: {error}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Registration failed: {str(error)}'}), 500
        finally:
            db.close()
    
    except Exception as error:
        print(f"Register outer error: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/login', methods=['POST'])
def login():
    """Login with email/password"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    db = db_session()
    
    try:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        password_hash_str = str(user.password_hash) if user.password_hash is not None else ''
        if not verify_password(password, password_hash_str):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Record login history (with flush)
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        user_name_str = str(user.name) if user.name is not None else None
        user_image_str = str(user.profile_image) if user.profile_image is not None else None
        db_operations.record_login_history(
            db,
            user_id=str(user.id),
            email=email,
            name=user_name_str,
            login_method='local',
            action='login',
            profile_image=user_image_str,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Final commit
        db.commit()
        
        # Create session token
        user_name = str(user.name) if user.name is not None else None
        session_token = create_session_token(str(user.id), user_name, Config.ONE_YEAR_MS)
        
        # Set cookie
        response = make_response(jsonify({
            'id': user.id,
            'email': user.email
        }), 200)
        
        response.set_cookie(
            Config.COOKIE_NAME,
            session_token,
            max_age=Config.ONE_YEAR_SECONDS,
            httponly=True,
            secure=False,
            samesite='Lax',
            path='/',
            domain=None
        )
        
        return response
        
    except Exception as error:
        print(f"Login failed: {error}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return jsonify({'error': f'Login failed: {str(error)}'}), 500
    finally:
        db.close()





@bp.route('/supabase', methods=['POST'])
def supabase_auth():
    """Supabase OAuth/token authentication"""
    data = request.get_json()
    access_token = data.get('accessToken')
    
    if not access_token:
        return jsonify({'error': 'Supabase access token is required'}), 400
    
    # Decode JWT token to get user info (without verification since it's from Supabase)
    try:
        # Decode without verification - we trust Supabase tokens
        decoded_token = jwt.decode(access_token, options={"verify_signature": False})
    except Exception as e:
        print(f"Error decoding token: {e}")
        return jsonify({'error': 'Invalid Supabase token'}), 401
    
    # Extract user info from decoded token
    user_id = decoded_token.get('sub')  # Supabase uses 'sub' for user ID
    email = decoded_token.get('email')
    user_metadata = decoded_token.get('user_metadata', {})
    name = user_metadata.get('full_name') or (email.split('@')[0] if email else 'User')
    profile_image = user_metadata.get('avatar_url')  # Google profile picture
    phone_number = user_metadata.get('phone')  # Phone from metadata
    date_of_birth = user_metadata.get('date_of_birth')  # DOB from metadata
    
    if not user_id or not email:
        return jsonify({'error': 'Invalid token: missing user ID or email'}), 401
    
    # Use Supabase UUID as user ID
    internal_user_id = f"supabase_{user_id}"
    
    db = db_session()
    
    try:
        # Upsert user (create or update) with all available profile data (with flush)
        db_operations.upsert_user(db, {
            'id': internal_user_id,
            'name': name,
            'email': email,
            'login_method': 'supabase',
            'profile_image': profile_image,
            'phone_number': phone_number,
            'date_of_birth': date_of_birth,
        })
        
        # Record login history (with flush)
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        db_operations.record_login_history(
            db,
            user_id=internal_user_id,
            email=email,
            name=name,
            login_method='supabase',
            action='login',
            profile_image=profile_image,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Transfer guest data if exists
        try:
            token = request.cookies.get(Config.COOKIE_NAME)
            if token:
                session = verify_session(token)
                if session:
                    guest_id = session.get('openId')
                    if guest_id and guest_id.startswith('guest_'):
                        db_operations.transfer_guest_data(db, guest_id, internal_user_id)
        except Exception as e:
            print(f"Failed to transfer guest data: {e}")
        
        # Final commit
        db.commit()
        
        # Create session token
        session_token = create_session_token(internal_user_id, name, Config.ONE_YEAR_MS)
        
        # Set cookie
        response = make_response(jsonify({
            'success': True,
            'user': {
                'id': internal_user_id,
                'email': email,
                'name': name,
                'profileImage': profile_image,
                'phoneNumber': phone_number,
                'dateOfBirth': date_of_birth,
            }
        }), 200)
        
        response.set_cookie(
            Config.COOKIE_NAME,
            session_token,
            max_age=Config.ONE_YEAR_SECONDS,
            httponly=True,
            secure=False,
            samesite='Lax',
            path='/',
            domain=None
        )
        
        return response
        
    except Exception as error:
        print(f"Supabase authentication failed: {error}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return jsonify({'error': f'Supabase authentication failed: {str(error)}'}), 500
    finally:
        db.close()


@bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    user = get_current_user()
    if user:
        user_id = str(user.id)
        db = db_session()
        try:
            # Mark user's active logins as inactive
            db_operations.mark_user_logout(db, user_id)
        finally:
            db.close()
    
    response = make_response(jsonify({'success': True}), 200)
    response.set_cookie(
        Config.COOKIE_NAME,
        '',
        max_age=0,
        httponly=True,
        secure=False,
        samesite='Lax',
        path='/',
        domain=None
    )
    return response


@bp.route('/delete-account', methods=['POST'])
def delete_account():
    """Delete current user account and all associated data"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Please login to delete account'}), 401
    
    user_id = str(user.id)
    email = user.email
    
    db = db_session()
    
    try:
        # Delete all user data
        # Delete messages and patient memory from conversations
        conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
        for conv in conversations:
            db.execute(delete(Message).where(Message.conversation_id == conv.id))
            db.execute(delete(PatientMemory).where(PatientMemory.conversation_id == conv.id))
        
        # Delete all conversations
        db.execute(delete(Conversation).where(Conversation.user_id == user_id))
        
        # Delete patient memory
        db.execute(delete(PatientMemory).where(PatientMemory.user_id == user_id))
        
        # Delete user preferences
        db.execute(delete(UserPreferences).where(UserPreferences.user_id == user_id))
        
        # Delete login history
        db.execute(delete(UserLoginHistory).where(UserLoginHistory.user_id == user_id))
        
        # Delete user record
        db.execute(delete(User).where(User.id == user_id))
        
        db.commit()
        
        # Clear session cookie
        response = make_response(jsonify({
            'success': True,
            'message': 'Account deleted successfully'
        }), 200)
        
        response.set_cookie(
            Config.COOKIE_NAME,
            '',
            max_age=0,
            httponly=True,
            secure=False,
            samesite='Lax',
            path='/',
            domain=None
        )
        
        print(f"[Delete Account] User deleted: {user_id} ({email})")
        return response
        
    except Exception as error:
        print(f"Delete account failed: {error}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return jsonify({'error': f'Failed to delete account: {str(error)}'}), 500
    finally:
        db.close()
