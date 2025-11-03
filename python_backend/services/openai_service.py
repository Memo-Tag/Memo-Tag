"""
OpenAI API Integration
Alternative to Perplexity for AI responses
Supports gpt-4o, gpt-4-turbo, gpt-3.5-turbo
"""

from openai import OpenAI
from typing import List, Dict, Any, Optional, Sequence
from config import Config

# Initialize OpenAI client
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Available OpenAI models
AVAILABLE_MODELS = [
    {
        "id": "gpt-3.5-turbo",
        "name": "GPT-3.5 Turbo",
        "description": "Fast & Cost-effective",
        "category": "fast"
    },
    {
        "id": "gpt-4-turbo",
        "name": "GPT-4 Turbo",
        "description": "Advanced Analysis",
        "category": "advanced"
    },
    {
        "id": "gpt-4o",
        "name": "GPT-4 Omni",
        "description": "Best for Medical Use",
        "category": "premium",
        "recommended": True
    }
]


def build_system_prompt(user_context: Optional[Dict[str, Any]] = None, is_medical: bool = True) -> str:
    """Build personalized system prompt based on user preferences"""
    
    prefs = user_context.get('preferences', {}) if user_context else {}
    profile = user_context.get('profile', {}) if user_context else {}
    
    # Casual conversation prompt
    if not is_medical:
        casual_prompt = "You are a friendly medical AI assistant having a casual conversation. "
        
        if profile.get('name'):
            casual_prompt += f"You are chatting with {profile['name']}. "
        if profile.get('address'):
            casual_prompt += f"They are from {profile['address']}. "
        if profile.get('bio'):
            casual_prompt += f"About them: {profile['bio']}. "
        
        # Apply age group
        age_group = prefs.get('age_group', prefs.get('ageGroup'))
        if age_group == 'young':
            casual_prompt += "\n**TONE**: You're chatting with someone YOUNG (18-35). Be super casual, modern, and relatable. "
        elif age_group == 'old':
            casual_prompt += "\n**TONE**: You're chatting with a SENIOR (60+). Be very patient, respectful, and warm. "
        
        # Apply response length
        response_length = prefs.get('response_length', prefs.get('responseLength'))
        if response_length == 'brief':
            casual_prompt += "\n\n**LENGTH**: Keep responses EXTREMELY brief - MAXIMUM 1-2 SHORT sentences. "
        elif response_length == 'comprehensive':
            casual_prompt += "\n\n**LENGTH**: Provide DETAILED responses. AT LEAST 4-5 sentences. "
        
        casual_prompt += "\n\n**IMPORTANT**: This is CASUAL conversation - NOT medical consultation.\n"
        casual_prompt += "- DO NOT search the web or provide citations\n"
        casual_prompt += "- Just chat naturally and warmly"
        
        return casual_prompt
    
    # Medical prompt
    prompt = "You are a trusted medical AI assistant. "
    
    if profile.get('name'):
        prompt += f"You are assisting {profile['name']}. "
    
    # Age group personalization
    age_group = prefs.get('age_group', prefs.get('ageGroup'))
    if age_group == 'young':
        prompt += "\n\n**IMPORTANT**: User is YOUNG (18-35). Use modern, casual, relatable language. "
    elif age_group == 'middle-aged':
        prompt += "\n\n**IMPORTANT**: User is MIDDLE-AGED (36-60). Professional yet warm tone. "
    elif age_group == 'old':
        prompt += "\n\n**IMPORTANT**: User is SENIOR (60+). Be EXTRA patient. Use VERY simple language. "
    
    # Response style
    response_style = prefs.get('response_style', prefs.get('responseStyle'))
    if response_style == 'simple':
        prompt += "\n\n**CRITICAL**: Keep responses EXTREMELY simple. Use only everyday words. "
    elif response_style == 'detailed':
        prompt += "\n\n**CRITICAL**: Provide VERY detailed, comprehensive explanations. "
    
    # Language complexity
    lang_complexity = prefs.get('language_complexity', prefs.get('languageComplexity'))
    if lang_complexity == 'simple':
        prompt += "\n\n**MANDATORY**: Avoid ALL medical jargon. Use ONLY simple words. "
    elif lang_complexity == 'technical':
        prompt += "\n\n**MANDATORY**: Use proper medical terminology and technical language. "
    
    # Medical terms
    include_terms = prefs.get('include_medical_terms', prefs.get('includeMedicalTerms'))
    if include_terms is False:
        prompt += "\nAvoid formal medical terms unless necessary. "
    
    # Response length
    response_length = prefs.get('response_length', prefs.get('responseLength'))
    if response_length == 'brief':
        prompt += "\n\n**LENGTH**: EXTREMELY brief - maximum 1-2 SHORT paragraphs. "
    elif response_length == 'concise':
        prompt += "\n\n**LENGTH**: Concise - 2-3 paragraphs maximum. "
    elif response_length == 'comprehensive':
        prompt += "\n\n**LENGTH**: COMPREHENSIVE responses with full details. Multiple paragraphs. "
    else:
        prompt += "\n\n**LENGTH**: Keep responses CONCISE (2-4 paragraphs maximum). "
    
    prompt += "\n\nGuidelines:\n"
    prompt += "- Always cite reliable medical sources when possible\n"
    prompt += "- Use clear, understandable language\n"
    prompt += "- Remind users to consult healthcare professionals\n"
    prompt += "- Format important points in **bold**"
    
    return prompt


def call_openai(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o",
    user_context: Optional[Dict[str, Any]] = None,
    user_message: Optional[str] = None,
    patient_memory_context: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Call OpenAI API
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: OpenAI model ID
        user_context: User profile and preferences
        user_message: Original user message
        patient_memory_context: List of patient memory entries to include
    
    Returns:
        Dict with 'content', 'model'
    """
    try:
        # Detect if medical query
        is_medical_query = is_medical_question(user_message) if user_message else True
        
        # Build system prompt
        system_prompt = build_system_prompt(user_context, is_medical_query)
        
        # Add patient memory context to system prompt if available
        if patient_memory_context and len(patient_memory_context) > 0:
            memory_text = "\n".join(patient_memory_context[:10])  # Limit to 10 entries
            system_prompt += f"\n\n**Patient Medical History** (from previous conversations):\n{memory_text}\n\nUse this patient history when relevant to personalize your response.\n"
        
        # Normalize messages (merge consecutive same-role)
        normalized = []
        for msg in messages:
            if normalized and normalized[-1]['role'] == msg['role'] and msg['role'] != 'system':
                normalized[-1]['content'] += f"\n{msg['content']}"
            else:
                normalized.append(msg.copy())
        
        # Build final messages with system prompt
        final_messages = [
            {"role": "system", "content": system_prompt}
        ]
        final_messages.extend([m for m in normalized if m['role'] != 'system'])
        
        # Call OpenAI API
        completion = openai_client.chat.completions.create(
            model=model,
            messages=final_messages,  # type: ignore
            temperature=0.3,  # Balanced for quality
            max_tokens=1000,  # Reasonable limit
        )
        
        content = completion.choices[0].message.content or ""
        
        return {
            "content": content,
            "citations": [],  # OpenAI doesn't provide citations like Perplexity
            "searchResults": [],  # OpenAI doesn't provide search results
            "model": model,
            "usage": {
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens
            } if completion.usage else None
        }
        
    except Exception as error:
        print(f"[OpenAI] API call failed: {error}")
        raise Exception("Failed to get response from OpenAI API")


def is_medical_question(question: str) -> bool:
    """Detect if the question is medical or casual conversation"""
    import re
    
    lower_question = question.lower().strip()
    
    # Casual conversation patterns
    casual_patterns = [
        r'^(hi|hello|hey|good morning|good afternoon|good evening|greetings)',
        r'^(how are you|how\'re you|how r u|what\'s up|wassup|sup)',
        r'^(how is it going|how\'s it going|how are things)',
        r'^(my name is|i am|i\'m|this is)',
        r'^(thank you|thanks|thx|ty|appreciate)',
        r'^(bye|goodbye|see you|talk later|gotta go)',
        r'^(ok|okay|yes|no|yeah|yep|nope|sure|alright|cool)$',
    ]
    
    # Check if casual
    for pattern in casual_patterns:
        if re.match(pattern, lower_question):
            return False
    
    # Default to medical
    return True
