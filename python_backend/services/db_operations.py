"""
Database operations
Replicates server/db.ts functionality
Now includes automatic vector embedding generation for semantic search
"""

from sqlalchemy import select, update, delete, desc
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from models import User, Conversation, Message, PatientMemory, UserPreferences, UserLoginHistory
from utils.auth import generate_id
from utils.datetime_utils import now_utc
from services.embedding_service import get_embedding_service


# ============================================
# User Management
# ============================================

def upsert_user(db: Session, user_data: Dict[str, Any]) -> None:
    """
    Create or update user
    
    Args:
        db: Database session
        user_data: User data dictionary with 'id' required
    """
    if not user_data.get('id'):
        raise ValueError("User ID is required for upsert")
    
    user_id = user_data['id']
    
    # Check if user exists
    existing = db.query(User).filter(User.id == user_id).first()
    
    if existing:
        # Update existing user
        for key, value in user_data.items():
            if hasattr(existing, key) and key != 'last_signed_in':
                setattr(existing, key, value)
        setattr(existing, 'last_signed_in', now_utc())
    else:
        # Create new user
        new_user = User(
            id=user_id,
            name=user_data.get('name'),
            email=user_data.get('email'),
            password_hash=user_data.get('password_hash'),
            login_method=user_data.get('login_method'),
            role=user_data.get('role', 'user'),
            profile_image=user_data.get('profile_image'),
            bio=user_data.get('bio'),
            date_of_birth=user_data.get('date_of_birth'),
            phone=user_data.get('phone'),
            address=user_data.get('address'),
            created_at=now_utc(),
            last_signed_in=now_utc()
        )
        db.add(new_user)
    
    db.flush()


def get_user(db: Session, user_id: str) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def transfer_guest_data(db: Session, guest_id: str, new_user_id: str) -> None:
    """
    Transfer data from guest user to registered user
    Moves conversations, patient memory, and preferences
    """
    # Move conversations
    db.execute(
        update(Conversation)
        .where(Conversation.user_id == guest_id)
        .values(user_id=new_user_id, is_guest=False, updated_at=now_utc())
    )
    
    # Move patient memory
    db.execute(
        update(PatientMemory)
        .where(PatientMemory.user_id == guest_id)
        .values(user_id=new_user_id, updated_at=now_utc())
    )
    
    # Handle user preferences
    existing_prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == new_user_id
    ).first()
    
    if existing_prefs:
        # Delete guest preferences
        db.execute(
            delete(UserPreferences).where(UserPreferences.user_id == guest_id)
        )
    else:
        # Transfer guest preferences
        db.execute(
            update(UserPreferences)
            .where(UserPreferences.user_id == guest_id)
            .values(user_id=new_user_id, updated_at=now_utc())
        )
    
    db.commit()


def record_login_history(
    db: Session,
    user_id: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
    login_method: str = 'local',
    action: str = 'login',
    profile_image: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """
    Record user login/signup in login history
    
    Args:
        db: Database session
        user_id: User ID
        email: User email
        name: User name
        login_method: Login method (local, supabase, google, etc.)
        action: Action type (login, signup, logout)
        profile_image: User profile image URL
        ip_address: Client IP address
        user_agent: Client user agent
    """
    try:
        login_record = UserLoginHistory(
            id=generate_id('login'),
            user_id=user_id,
            email=email,
            name=name,
            login_method=login_method,
            action=action,
            profile_image=profile_image,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=(action != 'logout'),
            timestamp=now_utc()
        )
        db.add(login_record)
        db.flush()  # Flush to DB but don't commit yet
    except Exception as e:
        print(f"Error recording login history: {e}")
        # Don't raise - let registration continue even if history fails


def get_user_login_history(db: Session, user_id: str, limit: int = 100) -> List[UserLoginHistory]:
    """
    Get login history for a user
    
    Args:
        db: Database session
        user_id: User ID
        limit: Max number of records to return
    
    Returns:
        List of login history records sorted by timestamp (newest first)
    """
    return db.query(UserLoginHistory).filter(
        UserLoginHistory.user_id == user_id
    ).order_by(desc(UserLoginHistory.timestamp)).limit(limit).all()


def get_all_active_logins(db: Session) -> List[UserLoginHistory]:
    """
    Get all active (logged-in) sessions across ALL users
    
    Returns:
        List of all active login records from all users
    """
    return db.query(UserLoginHistory).filter(
        UserLoginHistory.is_active == True
    ).order_by(desc(UserLoginHistory.timestamp)).all()


def mark_user_logout(db: Session, user_id: str) -> None:
    """
    Mark user's active login sessions as logged out
    
    Args:
        db: Database session
        user_id: User ID
    """
    db.execute(
        update(UserLoginHistory)
        .where(
            (UserLoginHistory.user_id == user_id) &
            (UserLoginHistory.is_active == True)
        )
        .values(is_active=False)
    )
    db.commit()


def cleanup_deleted_user_data(db: Session, email: str) -> None:
    """
    Clean up all data associated with a deleted user account
    This is called when registering a new account with an email that previously existed
    
    Args:
        db: Database session
        email: Email address to clean up
    """
    try:
        # Find all user IDs with this email from login history
        old_logins = db.query(UserLoginHistory).filter(UserLoginHistory.email == email).all()
        user_ids_to_clean = set(login.user_id for login in old_logins)
        
        # For each old user ID, delete associated data
        for user_id in user_ids_to_clean:
            # Delete conversations and their messages/memory
            conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
            for conv in conversations:
                # Delete messages for this conversation
                db.execute(delete(Message).where(Message.conversation_id == conv.id))
                # Delete patient memory for this conversation
                db.execute(delete(PatientMemory).where(PatientMemory.conversation_id == conv.id))
            
            # Delete all conversations for this user
            db.execute(delete(Conversation).where(Conversation.user_id == user_id))
            
            # Delete patient memory for this user
            db.execute(delete(PatientMemory).where(PatientMemory.user_id == user_id))
            
            # Delete user preferences
            db.execute(delete(UserPreferences).where(UserPreferences.user_id == user_id))
            
            # Delete user record if it still exists
            db.execute(delete(User).where(User.id == user_id))
        
        # Delete all login history for this email
        db.execute(delete(UserLoginHistory).where(UserLoginHistory.email == email))
        
        db.commit()
        print(f"[Cleanup] Successfully cleaned up data for email: {email}")
    except Exception as e:
        print(f"[Cleanup] Error cleaning up deleted user data: {e}")
        db.rollback()
        # Don't raise - allow registration to continue


# ============================================
# Conversation Management
# ============================================

def create_conversation(
    db: Session,
    user_id: Optional[str] = None,
    title: str = "New Conversation",
    is_guest: bool = False
) -> Conversation:
    """Create new conversation"""
    conversation = Conversation(
        id=generate_id('conv'),
        user_id=user_id,
        title=title,
        is_guest=is_guest,
        created_at=now_utc(),
        updated_at=now_utc()
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
    """Get conversation by ID"""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def get_user_conversations(db: Session, user_id: str) -> List[Conversation]:
    """Get all conversations for a user"""
    return db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(desc(Conversation.updated_at)).all()


def update_conversation_title(db: Session, conversation_id: str, title: str) -> None:
    """Update conversation title"""
    db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(title=title, updated_at=now_utc())
    )
    db.commit()


def delete_conversation(db: Session, conversation_id: str) -> None:
    """Delete conversation and related data"""
    # Delete patient memory
    db.execute(
        delete(PatientMemory).where(PatientMemory.conversation_id == conversation_id)
    )
    
    # Delete messages
    db.execute(
        delete(Message).where(Message.conversation_id == conversation_id)
    )
    
    # Delete conversation
    db.execute(
        delete(Conversation).where(Conversation.id == conversation_id)
    )
    
    db.commit()


# ============================================
# Message Management
# ============================================

def create_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    citations: Optional[List[str]] = None,
    search_results: Optional[List[Dict[str, Any]]] = None,
    model: Optional[str] = None,
    generate_embedding: bool = True
) -> Message:
    """
    Create new message with automatic embedding generation
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        role: Message role (user, assistant, system)
        content: Message content
        citations: Optional citation URLs
        search_results: Optional search result objects
        model: Model used to generate the message
        generate_embedding: Whether to generate vector embedding (default True)
    
    Returns:
        Created Message object with embedding
    """
    # Generate embedding for semantic search
    content_embedding = None
    if generate_embedding and content and content.strip():
        try:
            embedding_service = get_embedding_service()
            content_embedding = embedding_service.generate_message_embedding(
                content=content,
                role=role,
                citations=citations,
                search_results=search_results
            )
        except Exception as e:
            print(f"Warning: Failed to generate message embedding: {e}")
            # Continue without embedding - non-critical failure
    
    message = Message(
        id=generate_id('msg'),
        conversation_id=conversation_id,
        role=role,
        content=content,
        citations=citations,
        search_results=search_results,
        content_embedding=content_embedding,
        model=model,
        created_at=now_utc()
    )
    db.add(message)
    
    # Update conversation timestamp
    db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(updated_at=now_utc())
    )
    
    db.commit()
    db.refresh(message)
    return message


def get_conversation_messages(db: Session, conversation_id: str) -> List[Message]:
    """Get all messages for a conversation"""
    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()


# ============================================
# Patient Memory Management
# ============================================

def create_patient_memory(
    db: Session,
    user_id: str,
    entity_type: str,
    entity_name: str,
    relationships: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    conversation_id: Optional[str] = None,
    generate_embedding: bool = True
) -> PatientMemory:
    """
    Create patient memory entry with automatic embedding generation
    
    Args:
        db: Database session
        user_id: User ID
        entity_type: Type of entity (condition, symptom, medication, etc.)
        entity_name: Name of the entity
        relationships: Optional relationship objects
        metadata: Optional metadata dictionary
        conversation_id: Optional conversation ID
        generate_embedding: Whether to generate vector embedding (default True)
    
    Returns:
        Created PatientMemory object with embedding
    """
    # Generate embedding for semantic search
    content_embedding = None
    if generate_embedding and entity_name and entity_name.strip():
        try:
            embedding_service = get_embedding_service()
            content_embedding = embedding_service.generate_patient_memory_embedding(
                entity_name=entity_name,
                entity_type=entity_type,
                relationships=relationships,
                metadata=metadata
            )
        except Exception as e:
            print(f"Warning: Failed to generate patient memory embedding: {e}")
            # Continue without embedding - non-critical failure
    
    memory = PatientMemory(
        id=generate_id('mem'),
        user_id=user_id,
        entity_type=entity_type,
        entity_name=entity_name,
        relationships=relationships,
        entity_metadata=metadata,
        content_embedding=content_embedding,
        conversation_id=conversation_id,
        created_at=now_utc(),
        updated_at=now_utc()
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def get_user_patient_memory(db: Session, user_id: str) -> List[PatientMemory]:
    """Get all patient memory for a user"""
    return db.query(PatientMemory).filter(
        PatientMemory.user_id == user_id
    ).order_by(desc(PatientMemory.updated_at)).all()


def delete_patient_memory(db: Session, memory_id: str) -> None:
    """Delete specific patient memory"""
    db.execute(
        delete(PatientMemory).where(PatientMemory.id == memory_id)
    )
    db.commit()


# ============================================
# User Profile Management
# ============================================

def get_user_profile(db: Session, user_id: str) -> Optional[User]:
    """Get user profile"""
    return db.query(User).filter(User.id == user_id).first()


def update_user_profile(db: Session, user_id: str, updates: Dict[str, Any]) -> None:
    """Update user profile"""
    db.execute(
        update(User)
        .where(User.id == user_id)
        .values(**updates)
    )
    db.commit()


# ============================================
# User Preferences
# ============================================

def get_user_preferences(db: Session, user_id: str) -> Optional[UserPreferences]:
    """Get user preferences"""
    return db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()


def upsert_user_preferences(
    db: Session,
    user_id: str,
    preferences: Dict[str, Any]
) -> None:
    """Create or update user preferences"""
    existing = get_user_preferences(db, user_id)
    
    if existing:
        # Update existing
        for key, value in preferences.items():
            if hasattr(existing, key) and key != 'updated_at':
                setattr(existing, key, value)
        setattr(existing, 'updated_at', now_utc())
    else:
        # Create new
        new_prefs = UserPreferences(
            id=generate_id('pref'),
            user_id=user_id,
            preferred_model=preferences.get('preferred_model', 'sonar-pro'),
            theme=preferences.get('theme', 'light'),
            age_group=preferences.get('age_group', 'middle-aged'),
            response_style=preferences.get('response_style', 'professional'),
            language_complexity=preferences.get('language_complexity', 'moderate'),
            include_medical_terms=preferences.get('include_medical_terms', True),
            response_length=preferences.get('response_length', 'concise'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(new_prefs)
    
    db.commit()


# ============================================
# Vector Similarity Search
# ============================================

def search_similar_patient_memories(
    db: Session,
    query_text: str,
    user_id: str,
    match_threshold: float = 0.7,
    match_count: int = 5
) -> List[Dict[str, Any]]:
    """
    Search for similar patient memories using vector similarity
    
    Args:
        db: Database session
        query_text: Query text to search for
        user_id: User ID to filter memories
        match_threshold: Minimum similarity score (0-1, default 0.7)
        match_count: Maximum number of results (default 5)
    
    Returns:
        List of matching patient memory entries with similarity scores
    """
    try:
        # Generate query embedding
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.generate_embedding(query_text)
        
        # Use PostgreSQL function for similarity search
        from sqlalchemy import text
        
        query = text("""
            SELECT * FROM search_similar_patient_memories(
                :query_embedding::vector(384),
                :user_id,
                :match_threshold,
                :match_count
            )
        """)
        
        result = db.execute(query, {
            "query_embedding": query_embedding,
            "user_id": user_id,
            "match_threshold": match_threshold,
            "match_count": match_count
        })
        
        # Convert to list of dictionaries
        memories = []
        for row in result:
            memories.append({
                "id": row.id,
                "userId": row.user_id,
                "entityType": row.entity_type,
                "entityName": row.entity_name,
                "relationships": row.relationships,
                "metadata": row.metadata,
                "conversationId": row.conversation_id,
                "similarity": row.similarity
            })
        
        return memories
    
    except Exception as e:
        print(f"Error in similarity search: {e}")
        # Fallback to regular query without similarity
        return []


def search_similar_messages(
    db: Session,
    query_text: str,
    conversation_id: Optional[str] = None,
    match_threshold: float = 0.7,
    match_count: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for similar messages using vector similarity
    
    Args:
        db: Database session
        query_text: Query text to search for
        conversation_id: Optional conversation ID to filter (None = all conversations)
        match_threshold: Minimum similarity score (0-1, default 0.7)
        match_count: Maximum number of results (default 10)
    
    Returns:
        List of matching messages with similarity scores
    """
    try:
        # Generate query embedding
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.generate_embedding(query_text)
        
        # Use PostgreSQL function for similarity search
        from sqlalchemy import text
        
        query = text("""
            SELECT * FROM search_similar_messages(
                :query_embedding::vector(384),
                :conversation_id,
                :match_threshold,
                :match_count
            )
        """)
        
        result = db.execute(query, {
            "query_embedding": query_embedding,
            "conversation_id": conversation_id,
            "match_threshold": match_threshold,
            "match_count": match_count
        })
        
        # Convert to list of dictionaries
        messages = []
        for row in result:
            messages.append({
                "id": row.id,
                "conversationId": row.conversation_id,
                "role": row.role,
                "content": row.content,
                "citations": row.citations,
                "searchResults": row.search_results,
                "model": row.model,
                "createdAt": row.created_at.isoformat() if row.created_at else None,
                "similarity": row.similarity
            })
        
        return messages
    
    except Exception as e:
        print(f"Error in similarity search: {e}")
        # Fallback to empty results
        return []


def get_embedding_statistics(db: Session) -> Dict[str, Any]:
    """
    Get embedding coverage statistics
    
    Returns:
        Dictionary with embedding statistics for each table
    """
    try:
        from sqlalchemy import text
        
        query = text("SELECT * FROM get_embedding_stats()")
        result = db.execute(query)
        
        stats = {}
        for row in result:
            stats[row.table_name] = {
                "totalRows": row.total_rows,
                "embeddedRows": row.embedded_rows,
                "embeddingPercentage": float(row.embedding_percentage)
            }
        
        return stats
    
    except Exception as e:
        print(f"Error getting embedding stats: {e}")
        return {}


# ============================================
# Embedding Backfill (for existing data)
# ============================================

def backfill_message_embeddings(
    db: Session,
    batch_size: int = 100,
    conversation_id: Optional[str] = None
) -> int:
    """
    Generate embeddings for existing messages that don't have them
    
    Args:
        db: Database session
        batch_size: Number of messages to process per batch
        conversation_id: Optional conversation ID to limit backfill
    
    Returns:
        Number of messages updated with embeddings
    """
    # Query messages without embeddings
    query = db.query(Message).filter(Message.content_embedding.is_(None))
    
    if conversation_id:
        query = query.filter(Message.conversation_id == conversation_id)
    
    messages = query.limit(batch_size).all()
    
    if not messages:
        return 0
    
    try:
        embedding_service = get_embedding_service()
        updated_count = 0
        
        for message in messages:
            if message.content and message.content.strip():  # type: ignore
                try:
                    embedding = embedding_service.generate_message_embedding(
                        content=message.content,  # type: ignore
                        role=message.role,  # type: ignore
                        citations=message.citations,  # type: ignore
                        search_results=message.search_results  # type: ignore
                    )
                    message.content_embedding = embedding  # type: ignore
                    updated_count += 1
                except Exception as e:
                    print(f"Failed to generate embedding for message {message.id}: {e}")
        
        db.commit()
        return updated_count
    
    except Exception as e:
        print(f"Error backfilling message embeddings: {e}")
        db.rollback()
        return 0


def backfill_patient_memory_embeddings(
    db: Session,
    batch_size: int = 100,
    user_id: Optional[str] = None
) -> int:
    """
    Generate embeddings for existing patient memories that don't have them
    
    Args:
        db: Database session
        batch_size: Number of memories to process per batch
        user_id: Optional user ID to limit backfill
    
    Returns:
        Number of memories updated with embeddings
    """
    # Query patient memories without embeddings
    query = db.query(PatientMemory).filter(PatientMemory.content_embedding.is_(None))
    
    if user_id:
        query = query.filter(PatientMemory.user_id == user_id)
    
    memories = query.limit(batch_size).all()
    
    if not memories:
        return 0
    
    try:
        embedding_service = get_embedding_service()
        updated_count = 0
        
        for memory in memories:
            if memory.entity_name and memory.entity_name.strip():  # type: ignore
                try:
                    embedding = embedding_service.generate_patient_memory_embedding(
                        entity_name=memory.entity_name,  # type: ignore
                        entity_type=memory.entity_type,  # type: ignore
                        relationships=memory.relationships,  # type: ignore
                        metadata=memory.entity_metadata  # type: ignore
                    )
                    memory.content_embedding = embedding  # type: ignore
                    memory.updated_at = now_utc()  # type: ignore
                    updated_count += 1
                except Exception as e:
                    print(f"Failed to generate embedding for memory {memory.id}: {e}")
        
        db.commit()
        return updated_count
    
    except Exception as e:
        print(f"Error backfilling patient memory embeddings: {e}")
        db.rollback()
        return 0


def extract_and_save_patient_memory(
    db: Session,
    user_id: str,
    conversation_id: str,
    user_message: str,
    assistant_response: str
) -> int:
    """
    Extract medical entities from conversation and save to patient memory
    Uses AI to identify conditions, medications, people, and symptoms
    
    Args:
        db: Database session
        user_id: User ID
        conversation_id: Conversation ID
        user_message: User's message
        assistant_response: AI's response
    
    Returns:
        Number of entities extracted and saved
    """
    try:
        # Import here to avoid circular dependency
        import asyncio
        from services.perplexity import extract_patient_entities
        
        # Combine user message and assistant response for extraction
        conversation_text = f"User: {user_message}\n\nAssistant: {assistant_response}"
        
        # Extract entities using AI (async function, need to run in event loop)
        try:
            # Try to get current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a new task
                # This happens in background threads
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        extract_patient_entities(conversation_text)
                    )
                    entities = future.result(timeout=10)
            else:
                # If no loop running, run directly
                entities = asyncio.run(extract_patient_entities(conversation_text))
        except RuntimeError:
            # No event loop, create one
            entities = asyncio.run(extract_patient_entities(conversation_text))
        
        if not entities or not isinstance(entities, list):
            print("[Memory] No entities extracted from conversation")
            return 0
        
        # Get embedding service
        embedding_service = get_embedding_service()
        saved_count = 0
        
        for entity_data in entities:
            entity_type = entity_data.get('entityType', '')
            entity_name = entity_data.get('entityName', '')
            relationships = entity_data.get('relationships', [])
            metadata = entity_data.get('metadata', {})
            
            if not entity_name or not entity_type:
                continue
            
            # Check if entity already exists for this user
            existing = db.query(PatientMemory).filter(
                PatientMemory.user_id == user_id,
                PatientMemory.entity_name == entity_name,
                PatientMemory.entity_type == entity_type
            ).first()
            
            if existing:
                # Update existing entity (merge relationships)
                if relationships:
                    existing_rels = existing.relationships or []  # type: ignore
                    # Merge new relationships
                    for rel in relationships:
                        if rel not in existing_rels:
                            existing_rels.append(rel)
                    existing.relationships = existing_rels  # type: ignore
                
                if metadata:
                    existing_meta = existing.entity_metadata or {}  # type: ignore
                    existing_meta.update(metadata)
                    existing.entity_metadata = existing_meta  # type: ignore
                
                existing.updated_at = now_utc()  # type: ignore
                print(f"[Memory] Updated existing entity: {entity_name} ({entity_type})")
            else:
                # Generate embedding for new entity
                embedding = embedding_service.generate_patient_memory_embedding(
                    entity_name=entity_name,
                    entity_type=entity_type,
                    relationships=relationships,
                    metadata=metadata
                )
                
                # Create new patient memory
                new_memory = PatientMemory(
                    id=generate_id('pm'),
                    user_id=user_id,
                    conversation_id=conversation_id,
                    entity_type=entity_type,
                    entity_name=entity_name,
                    relationships=relationships if relationships else None,
                    entity_metadata=metadata if metadata else None,
                    content_embedding=embedding,
                    created_at=now_utc(),
                    updated_at=now_utc()
                )
                db.add(new_memory)
                saved_count += 1
                print(f"[Memory] Extracted new entity: {entity_name} ({entity_type})")
        
        db.commit()
        print(f"[Memory] Successfully saved {saved_count} new patient memory entities")
        return saved_count
        
    except Exception as e:
        print(f"[Memory] Failed to extract patient memory: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 0
