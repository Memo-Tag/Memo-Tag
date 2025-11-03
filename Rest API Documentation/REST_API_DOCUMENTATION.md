# MedChat REST API Documentation

**For Frontend Developers - Simple Step-by-Step Guide**

---

## 📌 Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication Endpoints](#1-authentication-endpoints)
3. [Conversation Endpoints](#2-conversation-endpoints)
4. [Chat Endpoints](#3-chat-endpoints)
5. [Profile Endpoints](#4-profile-endpoints)
6. [Preferences Endpoints](#5-preferences-endpoints)
7. [Patient Memory Endpoints](#6-patient-memory-endpoints)
8. [Complete Examples](#complete-examples)
9. [Error Handling](#error-handling)

---

## 🚀 Getting Started

### What You Need to Know

1. **Base URL**: `http://localhost:5000/api`
2. **Port**: Backend runs on port `5000`
3. **Authentication**: Session cookie named `app_session_id`
4. **Format**: All data is JSON

### Before Starting

Make sure:
- ✅ Backend is running: `python app.py` (in `python_backend` folder)
- ✅ Frontend is running: `npm run dev` (in `client` folder)
- ✅ Both can talk to each other

---

## 1. Authentication Endpoints

### Authentication Types

| Type | When to Use | What You Need |
|------|------------|--------------|
| **Register** | New user signing up | Email, Password, Name |
| **Login** | Existing user signing in | Email, Password |
| **Google OAuth** | Sign in with Google | Access token (auto from browser) |
| **Get Current User** | Check who is logged in | Session cookie (automatic) |
| **Logout** | User signs out | Session cookie (automatic) |

---

### 📝 **Endpoint 1.1: User Registration (Sign Up)**

**What it does**: Creates a new user account with email and password

```
METHOD: POST
PATH: /api/auth/register
REQUIRES AUTH: No (public endpoint)
```

#### Step 1: Prepare the data
```javascript
// In frontend (React)
const userData = {
  name: "John Doe",           // User's full name
  email: "john@example.com",  // Email address
  password: "SecurePass123!"  // Password (minimum 8 characters)
};
```

#### Step 2: Send the request
```javascript
// JavaScript/React example
const response = await fetch('http://localhost:5000/api/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'  // Tell server we're sending JSON
  },
  credentials: 'include',  // Important! Send cookies automatically
  body: JSON.stringify(userData)
});

const result = await response.json();
```

#### Step 3: What you get back (Response)
```javascript
// Success response (201 Created)
{
  "id": "user_550b5072-a7f8-4caa-b5aa-66d47c8a47da",
  "email": "john@example.com"
}

// The browser automatically gets a session cookie: app_session_id ✅
```

#### Test with CURL (for testing)
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

---

### 📝 **Endpoint 1.2: User Login**

**What it does**: Authenticates an existing user

```
METHOD: POST
PATH: /api/auth/login
REQUIRES AUTH: No (public endpoint)
```

#### Step 1: Prepare the data
```javascript
const loginData = {
  email: "john@example.com",
  password: "SecurePass123!"
};
```

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  credentials: 'include',  // Don't forget this!
  body: JSON.stringify(loginData)
});

const result = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "id": "user_550b5072-a7f8-4caa-b5aa-66d47c8a47da",
  "email": "john@example.com"
}

// Session cookie automatically set! ✅
```

#### Test with CURL
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }' \
  -c cookies.txt  # Save cookies to file
```

---

### 📝 **Endpoint 1.3: Google OAuth Authentication**

**What it does**: Authenticates user via Google and auto-fetches their profile

```
METHOD: POST
PATH: /api/auth/supabase
REQUIRES AUTH: No (uses access token)
```

#### How it works
1. **In Browser**: User clicks "Continue with Google"
2. **Google Login**: User signs in with Google account
3. **Browser gets token**: Supabase creates access token
4. **Frontend sends token**: To `/api/auth/supabase` endpoint
5. **Backend processes**: Extracts user info from token
6. **Session created**: User is logged in ✅

#### Step 1: Google login already happens in browser
```javascript
// This is handled by the frontend login page automatically
// User sees: "Continue with Google" button → clicks → completes Google login → redirects
```

#### Step 2: Frontend automatically sends token
```javascript
// The frontend already does this for you!
// After Google authenticates, it calls:
const response = await fetch('http://localhost:5000/api/auth/supabase', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  credentials: 'include',
  body: JSON.stringify({
    accessToken: token  // From Supabase after Google auth
  })
});
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "success": true,
  "user": {
    "id": "supabase_550b5072-a7f8-4caa-b5aa-66d47c8a47da",
    "email": "john@gmail.com",
    "name": "John Doe",
    "profileImage": "https://lh3.googleusercontent.com/...",  // Google profile pic
    "phoneNumber": "+1234567890",  // If in Google account
    "dateOfBirth": "1990-01-15"    // If in Google account
  }
}

// Auto-filled profile data! ✅
// Session cookie set! ✅
```

#### Test with CURL (manual)
```bash
# 1. Complete Google auth in browser first
# 2. Get the access token from browser console
# 3. Then run this:
curl -X POST http://localhost:5000/api/auth/supabase \
  -H "Content-Type: application/json" \
  -d '{
    "accessToken": "PASTE_TOKEN_FROM_GOOGLE_HERE"
  }'
```

---

### 📝 **Endpoint 1.4: Get Current User Info**

**What it does**: Returns the logged-in user's information

```
METHOD: GET
PATH: /api/auth/me
REQUIRES AUTH: Yes (session cookie needed)
```

#### Step 1: No data to prepare
```javascript
// Just make the request - cookie is sent automatically
```

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/auth/me', {
  method: 'GET',
  credentials: 'include'  // Send session cookie automatically
});

const currentUser = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "id": "user_550b5072-a7f8-4caa-b5aa-66d47c8a47da",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "user",
  "loginMethod": "supabase",
  "profileImage": "https://...",
  "lastSignedIn": "2025-10-29T10:30:00"
}
```

#### Test with CURL
```bash
curl -X GET http://localhost:5000/api/auth/me \
  -H "Cookie: app_session_id=YOUR_SESSION_COOKIE"
```

#### Use Case: Check if user is logged in
```javascript
// Frontend: Check login status on app start
useEffect(() => {
  const checkLogin = async () => {
    const response = await fetch('http://localhost:5000/api/auth/me', {
      credentials: 'include'
    });
    
    if (response.ok) {
      const user = await response.json();
      console.log('User is logged in:', user.name);
      setUser(user);
    } else {
      console.log('User not logged in');
      setUser(null);
    }
  };
  
  checkLogin();
}, []);
```

---

### 📝 **Endpoint 1.5: Logout**

**What it does**: Logs out the user and clears the session

```
METHOD: POST
PATH: /api/auth/logout
REQUIRES AUTH: Yes (session cookie needed)
```

#### Step 1: No data to prepare

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/auth/logout', {
  method: 'POST',
  credentials: 'include'  // Send session cookie
});

const result = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "success": true
}

// Session cookie deleted! ✅
// User is logged out! ✅
```

#### Test with CURL
```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Cookie: app_session_id=YOUR_SESSION_COOKIE"
```

---

### 📝 **Endpoint 1.6: Delete Account (PERMANENT)**

**What it does**: Permanently deletes the user account and ALL associated data

⚠️ **WARNING**: This action is **IRREVERSIBLE**. Once deleted, cannot be undone!

```
METHOD: POST
PATH: /api/auth/delete-account
REQUIRES AUTH: Yes (session cookie needed)
```

#### What Gets Deleted:
- ✓ User account record
- ✓ All conversations
- ✓ All messages
- ✓ All patient memory entries
- ✓ All user preferences
- ✓ All login history
- ✓ Session cookie

#### Step 1: No data to prepare

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/auth/delete-account', {
  method: 'POST',
  credentials: 'include'  // Send session cookie
});

const result = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "success": true,
  "message": "Account deleted successfully"
}

// Account completely removed from database! ✅
// Can re-register with same email ✅
```

#### Test with CURL
```bash
curl -X POST http://localhost:5000/api/auth/delete-account \
  -H "Cookie: app_session_id=YOUR_SESSION_COOKIE"
```

#### Use Cases:
- Clean up test accounts created during development
- Remove all user data from Supabase database
- No data recovery possible
- Can re-register with same email after deletion

---

## 2. Conversation Endpoints

### What is a Conversation?

- A **conversation** is a chat thread
- It contains multiple **messages** (user + AI)
- Each conversation has a **title** (user can edit)
- Users can have multiple conversations

---

### 📝 **Endpoint 2.1: Create New Conversation**

**What it does**: Starts a new chat conversation

```
METHOD: POST
PATH: /api/conversations
REQUIRES AUTH: No (optional - works for guests too)
```

#### Step 1: Prepare the data
```javascript
const conversationData = {
  title: "Diabetes Management"  // Optional - auto-generated if not provided
};
```

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/conversations', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  credentials: 'include',
  body: JSON.stringify(conversationData)
});

const data = await response.json();
const conversationId = data.conversation.id;  // Save this! You'll need it
```

#### Step 3: What you get back
```javascript
// Success response (201 Created)
{
  "conversation": {
    "id": "conv_abc123def456",              // 👈 SAVE THIS!
    "userId": "user_550b5072-a7f8-4caa",
    "title": "Diabetes Management",
    "isGuest": false,
    "createdAt": "2025-10-29T10:30:00",
    "updatedAt": "2025-10-29T10:30:00"
  }
}
```

#### Test with CURL
```bash
curl -X POST http://localhost:5000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Diabetes Management"
  }'
```

---

### 📝 **Endpoint 2.2: Get All Conversations**

**What it does**: Lists all conversations for the logged-in user

```
METHOD: GET
PATH: /api/conversations
REQUIRES AUTH: Yes
```

#### Step 1: No data to prepare

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/conversations', {
  method: 'GET',
  credentials: 'include'
});

const conversations = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
[
  {
    "id": "conv_abc123",
    "title": "Diabetes Management",
    "createdAt": "2025-10-29T10:30:00",
    "updatedAt": "2025-10-29T10:30:00"
  },
  {
    "id": "conv_def456",
    "title": "Heart Disease Prevention",
    "createdAt": "2025-10-28T15:20:00",
    "updatedAt": "2025-10-28T15:20:00"
  }
]
```

#### Test with CURL
```bash
curl -X GET http://localhost:5000/api/conversations \
  -H "Cookie: app_session_id=YOUR_SESSION_COOKIE"
```

---

### 📝 **Endpoint 2.3: Get Conversation with Messages**

**What it does**: Gets a specific conversation and all its messages

```
METHOD: GET
PATH: /api/conversations/{conversation_id}
REQUIRES AUTH: No
```

#### Step 1: Need conversation ID from previous step

#### Step 2: Send the request
```javascript
const conversationId = "conv_abc123";  // From endpoint 2.1

const response = await fetch(
  `http://localhost:5000/api/conversations/${conversationId}`,
  {
    method: 'GET',
    credentials: 'include'
  }
);

const data = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "conversation": {
    "id": "conv_abc123",
    "title": "Diabetes Management",
    "createdAt": "2025-10-29T10:30:00"
  },
  "messages": [
    {
      "id": "msg_123",
      "conversationId": "conv_abc123",
      "role": "user",
      "content": "What are symptoms of diabetes?",
      "createdAt": "2025-10-29T10:35:00"
    },
    {
      "id": "msg_124",
      "conversationId": "conv_abc123",
      "role": "assistant",
      "content": "Symptoms of diabetes include...",
      "citations": [
        {
          "title": "Diabetes Overview",
          "url": "https://...",
          "source": "Medical Database"
        }
      ],
      "searchResults": [...],
      "createdAt": "2025-10-29T10:35:30"
    }
  ]
}
```

#### Test with CURL
```bash
curl -X GET http://localhost:5000/api/conversations/conv_abc123
```

---

### 📝 **Endpoint 2.4: Update Conversation Title**

**What it does**: Changes the title of a conversation

```
METHOD: PUT
PATH: /api/conversations/{conversation_id}
REQUIRES AUTH: No
```

#### Step 1: Prepare the data
```javascript
const updates = {
  title: "New Title: Managing Type 2 Diabetes"
};
```

#### Step 2: Send the request
```javascript
const conversationId = "conv_abc123";

const response = await fetch(
  `http://localhost:5000/api/conversations/${conversationId}`,
  {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  }
);

const result = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "success": true
}
```

#### Test with CURL
```bash
curl -X PUT http://localhost:5000/api/conversations/conv_abc123 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Title: Managing Type 2 Diabetes"
  }'
```

---

### 📝 **Endpoint 2.5: Delete Conversation**

**What it does**: Deletes a conversation and all its messages

```
METHOD: DELETE
PATH: /api/conversations/{conversation_id}
REQUIRES AUTH: No
```

#### Step 1: No data to prepare

#### Step 2: Send the request
```javascript
const conversationId = "conv_abc123";

const response = await fetch(
  `http://localhost:5000/api/conversations/${conversationId}`,
  {
    method: 'DELETE'
  }
);

const result = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "success": true
}

// Conversation deleted! ✅
```

#### Test with CURL
```bash
curl -X DELETE http://localhost:5000/api/conversations/conv_abc123
```

---

## 3. Chat Endpoints

### What is Chat?

- **Send Message**: User sends a message → AI responds
- **Get Models**: Shows available AI models to use

---

### 📝 **Endpoint 3.1: Send Message (Get AI Response)**

**What it does**: Sends a user message and gets AI response with citations

```
METHOD: POST
PATH: /api/chat/send
REQUIRES AUTH: No (optional for history)
```

#### Step 1: Prepare the data
```javascript
const messageData = {
  conversationId: "conv_abc123",  // Required if you want to save messages
  message: "What are symptoms of Type 2 diabetes?",
  model: "sonar"  // Available: sonar, sonar-pro
};
```

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/chat/send', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  credentials: 'include',
  body: JSON.stringify(messageData)
});

const chatResponse = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "message": {
    "id": "msg_xyz789",
    "conversationId": "conv_abc123",
    "role": "assistant",
    "content": "Type 2 diabetes symptoms include increased thirst, frequent urination, fatigue, and blurred vision...",
    "model": "sonar",
    "createdAt": "2025-10-29T10:35:30"
  },
  "citations": [
    {
      "title": "Diabetes Symptoms",
      "url": "https://medicaldb.com/diabetes",
      "source": "Medical Database"
    }
  ],
  "searchResults": [
    {
      "title": "Type 2 Diabetes Overview",
      "url": "https://...",
      "snippet": "Type 2 diabetes is..."
    }
  ]
}
```

#### Tips
- ⚡ Response time: **Under 2 seconds** (optimized!)
- 📚 Citations: Shows sources used by AI
- 🔍 Search Results: Where AI found the information

#### Test with CURL
```bash
curl -X POST http://localhost:5000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "conversationId": "conv_abc123",
    "message": "What are symptoms of Type 2 diabetes?",
    "model": "sonar"
  }'
```

---

### 📝 **Endpoint 3.2: Get Available AI Models**

**What it does**: Lists all available AI models

```
METHOD: GET
PATH: /api/chat/models
REQUIRES AUTH: No
```

#### Step 1: No data to prepare

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/chat/models', {
  method: 'GET'
});

const models = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
[
  {
    "id": "sonar",
    "name": "Sonar (Fast)",
    "category": "fast",
    "description": "Fast responses, good quality"
  },
  {
    "id": "sonar-pro",
    "name": "Sonar Pro (Best Quality)",
    "category": "premium",
    "description": "Best quality responses, slightly slower"
  }
]
```

#### Test with CURL
```bash
curl -X GET http://localhost:5000/api/chat/models
```

---

## 4. Profile Endpoints

### What is a Profile?

- **Name**: User's full name
- **Email**: Email address
- **Phone**: Phone number
- **Date of Birth**: Birthday
- **Bio**: Short biography
- **Address**: Physical address
- **Profile Image**: Avatar/picture

---

### 📝 **Endpoint 4.1: Get User Profile**

**What it does**: Retrieves the logged-in user's profile

```
METHOD: GET
PATH: /api/profile
REQUIRES AUTH: Yes
```

#### Step 1: No data to prepare

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/profile', {
  method: 'GET',
  credentials: 'include'
});

const profile = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "id": "user_550b5072-a7f8-4caa-b5aa-66d47c8a47da",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1 (555) 123-4567",
  "dateOfBirth": "1990-01-15",
  "bio": "Software engineer interested in healthcare",
  "address": "123 Main St, City, State",
  "profileImage": "https://..."
}
```

#### Special Notes
- **For Google OAuth Users**: Name, Email, and Phone are auto-populated from Google! 
- You can edit any field afterwards

#### Test with CURL
```bash
curl -X GET http://localhost:5000/api/profile \
  -H "Cookie: app_session_id=YOUR_SESSION_COOKIE"
```

---

### 📝 **Endpoint 4.2: Update User Profile**

**What it does**: Updates the logged-in user's profile information

```
METHOD: PUT
PATH: /api/profile
REQUIRES AUTH: Yes
```

#### Step 1: Prepare the data (only include fields to update)
```javascript
const profileUpdates = {
  name: "John Smith",
  phone: "+1 (555) 987-6543",
  dateOfBirth: "1990-01-15",
  bio: "Healthcare technology enthusiast",
  address: "456 Oak Ave, Another City, State"
  // Don't include fields you don't want to update
};
```

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/profile', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json'
  },
  credentials: 'include',
  body: JSON.stringify(profileUpdates)
});

const result = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "success": true
}

// Profile updated! ✅
```

#### Test with CURL
```bash
curl -X PUT http://localhost:5000/api/profile \
  -H "Content-Type: application/json" \
  -H "Cookie: app_session_id=YOUR_SESSION_COOKIE" \
  -d '{
    "name": "John Smith",
    "phone": "+1 (555) 987-6543",
    "dateOfBirth": "1990-01-15",
    "bio": "Healthcare technology enthusiast",
    "address": "456 Oak Ave, Another City, State"
  }'
```

---

## 5. Preferences Endpoints

### What are Preferences?

User can customize how the AI responds:
- **Age Group**: young, middle-aged, senior
- **Response Style**: simple, professional, detailed
- **Language Complexity**: simple, moderate, technical
- **Response Length**: brief, concise, comprehensive
- **Include Medical Terms**: yes/no
- **Preferred Model**: sonar, sonar-pro

---

### 📝 **Endpoint 5.1: Get User Preferences**

**What it does**: Gets the user's AI response preferences

```
METHOD: GET
PATH: /api/preferences
REQUIRES AUTH: Yes
```

#### Step 1: No data to prepare

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/preferences', {
  method: 'GET',
  credentials: 'include'
});

const preferences = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "preferredModel": "sonar-pro",
  "theme": "dark",
  "ageGroup": "middle-aged",
  "responseStyle": "professional",
  "languageComplexity": "moderate",
  "includeMedicalTerms": true,
  "responseLength": "concise"
}
```

#### Test with CURL
```bash
curl -X GET http://localhost:5000/api/preferences \
  -H "Cookie: app_session_id=YOUR_SESSION_COOKIE"
```

---

### 📝 **Endpoint 5.2: Update User Preferences**

**What it does**: Updates the user's AI response preferences

```
METHOD: PUT
PATH: /api/preferences
REQUIRES AUTH: Yes
```

#### Step 1: Prepare the data
```javascript
const preferenceUpdates = {
  preferredModel: "sonar",
  theme: "light",
  ageGroup: "young",
  responseStyle: "simple",
  languageComplexity: "simple",
  includeMedicalTerms: false,
  responseLength: "brief"
};
```

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/preferences', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json'
  },
  credentials: 'include',
  body: JSON.stringify(preferenceUpdates)
});

const result = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "success": true
}

// Preferences updated! ✅
// AI will now customize responses based on these preferences! ✅
```

#### Test with CURL
```bash
curl -X PUT http://localhost:5000/api/preferences \
  -H "Content-Type: application/json" \
  -H "Cookie: app_session_id=YOUR_SESSION_COOKIE" \
  -d '{
    "preferredModel": "sonar",
    "ageGroup": "young",
    "responseStyle": "simple"
  }'
```

---

## 6. Patient Memory Endpoints

### What is Patient Memory?

- AI automatically learns about the user's health
- Example: "User has Type 2 Diabetes"
- Stored after conversations
- Used to personalize AI responses
- User can delete individual memories or clear all

---

### 📝 **Endpoint 6.1: Get Patient Memory**

**What it does**: Lists all stored patient health information

```
METHOD: GET
PATH: /api/memory/patient
REQUIRES AUTH: Yes
```

#### Step 1: No data to prepare

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/memory/patient', {
  method: 'GET',
  credentials: 'include'
});

const memories = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
[
  {
    "id": "mem_123abc",
    "userId": "user_550b5072",
    "entityType": "condition",
    "entityName": "Type 2 Diabetes",
    "relationships": "managed with metformin",
    "metadata": { ... },
    "conversationId": "conv_abc123",
    "createdAt": "2025-10-29T10:35:00"
  },
  {
    "id": "mem_456def",
    "userId": "user_550b5072",
    "entityType": "symptom",
    "entityName": "Frequent thirst",
    "relationships": "associated with diabetes",
    "createdAt": "2025-10-29T10:35:00"
  }
]
```

#### Types of Memories
- **condition**: Health condition (diabetes, hypertension, etc.)
- **symptom**: Symptoms (fever, pain, etc.)
- **medication**: Medicines user is taking
- **allergy**: Allergies
- **procedure**: Medical procedures
- **lifestyle**: Lifestyle factors

#### Test with CURL
```bash
curl -X GET http://localhost:5000/api/memory/patient \
  -H "Cookie: app_session_id=YOUR_SESSION_COOKIE"
```

---

### 📝 **Endpoint 6.2: Delete Specific Memory**

**What it does**: Removes a single memory entry

```
METHOD: DELETE
PATH: /api/memory/patient/{memory_id}
REQUIRES AUTH: Yes
```

#### Step 1: Get memory ID from endpoint 6.1

#### Step 2: Send the request
```javascript
const memoryId = "mem_123abc";

const response = await fetch(
  `http://localhost:5000/api/memory/patient/${memoryId}`,
  {
    method: 'DELETE',
    credentials: 'include'
  }
);

const result = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "success": true
}

// Memory deleted! ✅
```

#### Test with CURL
```bash
curl -X DELETE http://localhost:5000/api/memory/patient/mem_123abc \
  -H "Cookie: app_session_id=YOUR_SESSION_COOKIE"
```

---

### 📝 **Endpoint 6.3: Clear All Patient Memory**

**What it does**: Deletes ALL patient health memories

```
METHOD: POST
PATH: /api/memory/patient/clear
REQUIRES AUTH: Yes
```

#### ⚠️ Warning: This deletes everything! Be sure!

#### Step 1: No data to prepare

#### Step 2: Send the request
```javascript
const response = await fetch('http://localhost:5000/api/memory/patient/clear', {
  method: 'POST',
  credentials: 'include'
});

const result = await response.json();
```

#### Step 3: What you get back
```javascript
// Success response (200 OK)
{
  "success": true
}

// ALL memories deleted! ⚠️
```

#### Test with CURL
```bash
curl -X POST http://localhost:5000/api/memory/patient/clear \
  -H "Cookie: app_session_id=YOUR_SESSION_COOKIE"
```

---

## ✅ Complete Examples

### Complete Example 1: User Signup Flow

```javascript
// Step 1: User clicks "Sign Up" button
const signup = async () => {
  // Step 2: Collect user data from form
  const userData = {
    name: document.getElementById('name').value,
    email: document.getElementById('email').value,
    password: document.getElementById('password').value
  };
  
  // Step 3: Send to backend
  try {
    const response = await fetch('http://localhost:5000/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(userData)
    });
    
    if (response.ok) {
      const user = await response.json();
      console.log('✅ Signed up successfully!');
      console.log('User ID:', user.id);
      
      // Step 4: Redirect to chat
      window.location.href = '/chat';
    } else {
      console.error('❌ Signup failed');
    }
  } catch (error) {
    console.error('Error:', error);
  }
};
```

---

### Complete Example 2: Chat Flow

```javascript
// Step 1: User is logged in, create conversation
const startChat = async () => {
  const convResponse = await fetch('http://localhost:5000/api/conversations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ title: 'New Chat' })
  });
  
  const convData = await convResponse.json();
  const conversationId = convData.conversation.id;
  console.log('📋 Conversation created:', conversationId);
  
  // Step 2: User types message and clicks send
  const userMessage = document.getElementById('messageInput').value;
  
  // Step 3: Send message to AI
  const chatResponse = await fetch('http://localhost:5000/api/chat/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      conversationId: conversationId,
      message: userMessage,
      model: 'sonar'
    })
  });
  
  const chatData = await chatResponse.json();
  console.log('🤖 AI Response:', chatData.message.content);
  console.log('📚 Citations:', chatData.citations);
  
  // Step 4: Display response to user
  displayMessage('user', userMessage);
  displayMessage('assistant', chatData.message.content);
};
```

---

### Complete Example 3: Update Profile

```javascript
// After Google OAuth login, auto-filled profile is shown
const updateProfile = async () => {
  const updates = {
    phone: document.getElementById('phone').value,
    dateOfBirth: document.getElementById('dob').value,
    bio: document.getElementById('bio').value,
    address: document.getElementById('address').value
  };
  
  const response = await fetch('http://localhost:5000/api/profile', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(updates)
  });
  
  if (response.ok) {
    console.log('✅ Profile updated!');
  }
};
```

---

## ❌ Error Handling

### Common Errors and Fixes

| Error Code | Meaning | How to Fix |
|-----------|---------|-----------|
| **400** | Bad Request (missing data) | Check you sent all required fields |
| **401** | Unauthorized (not logged in) | Add `credentials: 'include'` to your fetch |
| **404** | Not Found (wrong endpoint) | Check the URL path spelling |
| **500** | Server Error | Check backend logs: `python app.py` |

---

### Example Error Handling

```javascript
const sendRequest = async (endpoint, options) => {
  try {
    const response = await fetch(`http://localhost:5000/api${endpoint}`, {
      ...options,
      credentials: 'include'
    });
    
    // Check for errors
    if (!response.ok) {
      const error = await response.json();
      console.error(`❌ Error ${response.status}:`, error.error);
      
      // Handle specific errors
      if (response.status === 401) {
        console.log('You need to login first!');
        window.location.href = '/login';
      } else if (response.status === 404) {
        console.log('Resource not found!');
      }
      
      return null;
    }
    
    const data = await response.json();
    console.log('✅ Success:', data);
    return data;
    
  } catch (error) {
    console.error('🔥 Network error:', error);
    return null;
  }
};

// Usage
await sendRequest('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
```

---

## 🎯 Quick Reference

### Authentication (Login/Signup)
```
Register: POST /api/auth/register
Login: POST /api/auth/login
Google OAuth: POST /api/auth/supabase
Get Current User: GET /api/auth/me
Logout: POST /api/auth/logout
```

### Conversations
```
Create: POST /api/conversations
List All: GET /api/conversations
Get One: GET /api/conversations/{id}
Update: PUT /api/conversations/{id}
Delete: DELETE /api/conversations/{id}
```

### Chat
```
Send Message: POST /api/chat/send
Get Models: GET /api/chat/models
```

### Profile
```
Get: GET /api/profile
Update: PUT /api/profile
```

### Preferences
```
Get: GET /api/preferences
Update: PUT /api/preferences
```

### Patient Memory
```
Get All: GET /api/memory/patient
Delete One: DELETE /api/memory/patient/{id}
Clear All: POST /api/memory/patient/clear
```

---

## 🚀 Summary for Frontend Developers

1. **Read this document** - Understand each endpoint
2. **Use CURL to test** - Make sure endpoints work
3. **Implement in React** - Use `fetch()` with examples above
4. **Handle errors** - Check response status codes
5. **Add credentials** - Always include `credentials: 'include'` for auth endpoints
6. **Save IDs** - Store conversation_id and user_id for later use

**You're ready to build the frontend! 🎉**

---

**Questions?** Check the complete examples or test with CURL first!
