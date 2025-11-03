# REST API Documentation - Quick Summary

**Everything Frontend Developers Need to Know**

---

## 📚 Documentation Files Created

| File | Purpose | Audience |
|------|---------|----------|
| **REST_API_DOCUMENTATION.md** | Complete API endpoint reference | Frontend/Backend devs |
| **FRONTEND_INTEGRATION_GUIDE.md** | Step-by-step integration guide | Frontend developers |
| **test_api.sh** | Automated CURL testing script | Everyone |

---

## 🚀 Quick Start (5 Minutes)

### 1. Read the Documentation
```bash
# Read main API documentation
cat REST_API_DOCUMENTATION.md

# Read frontend integration guide
cat FRONTEND_INTEGRATION_GUIDE.md
```

### 2. Test the API
```bash
# Make test script executable
chmod +x test_api.sh

# Run all tests
./test_api.sh
```

### 3. Verify Backend is Running
```bash
# Should return: {"status":"ok","message":"MedChat API"}
curl http://localhost:5000/api/health
```

---

## 📋 All Available Endpoints

### Authentication (6 endpoints)
```
POST   /api/auth/register              - Create account
POST   /api/auth/login                 - Login with email/password
POST   /api/auth/supabase              - Login with Google (OAuth)
GET    /api/auth/me                    - Get current user + active sessions
POST   /api/auth/logout                - Logout
POST   /api/auth/delete-account        - PERMANENTLY delete account & all data
```

### Conversations (5 endpoints)
```
POST   /api/conversations              - Create new chat
GET    /api/conversations              - List all chats
GET    /api/conversations/{id}         - Get chat with messages
PUT    /api/conversations/{id}         - Update chat title
DELETE /api/conversations/{id}         - Delete chat
```

### Chat (2 endpoints)
```
POST   /api/chat/send                  - Send message (get AI response)
GET    /api/chat/models                - Get available AI models
```

### Profile (2 endpoints)
```
GET    /api/profile                    - Get user profile
PUT    /api/profile                    - Update user profile
```

### Preferences (2 endpoints)
```
GET    /api/preferences                - Get AI preferences
PUT    /api/preferences                - Update AI preferences
```

### Patient Memory (3 endpoints)
```
GET    /api/memory/patient             - Get all health memories
DELETE /api/memory/patient/{id}        - Delete single memory
POST   /api/memory/patient/clear       - Delete all memories
```

**Total: 20 endpoints**

---

## 🔑 Key Concepts

### Base URL
```
http://localhost:5000/api
```

### Authentication
- Session cookie: `app_session_id`
- Always add `credentials: 'include'` in fetch requests
- Cookie set automatically on login/register

### Response Format
```javascript
// Success (200, 201)
{
  "data": "value",
  "nested": {
    "key": "value"
  }
}

// Error (400, 401, 404, 500)
{
  "error": "Error message here"
}
```

### Status Codes
- `200` - OK
- `201` - Created
- `400` - Bad request (missing data)
- `401` - Unauthorized (not logged in)
- `404` - Not found
- `500` - Server error

---

## 💡 Example: Login Flow

### CURL
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### JavaScript
```javascript
const response = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include', // ✅ Don't forget!
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const user = await response.json();
console.log('Logged in:', user.email);
```

---

## 📝 Simple Frontend Template

### 1. Create API Client
```typescript
// src/lib/api-client.ts
export async function apiCall(endpoint, options = {}) {
  const response = await fetch(`http://localhost:5000/api${endpoint}`, {
    credentials: 'include',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
  
  if (!response.ok) {
    throw new Error((await response.json()).error);
  }
  
  return response.json();
}
```

### 2. Use in Component
```typescript
// src/pages/Login.tsx
import { apiCall } from '@/lib/api-client';

async function handleLogin(email, password) {
  try {
    const user = await apiCall('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    
    console.log('✅ Logged in:', user.email);
    // Redirect to chat
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}
```

---

## ✅ Testing Endpoints

### Test Without Coding
```bash
# 1. Check backend is alive
curl http://localhost:5000/api/health

# 2. Register a test user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "name": "Test",
    "email": "test@medchat.com",
    "password": "Pass123!"
  }'

# 3. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "email": "test@medchat.com",
    "password": "Pass123!"
  }'

# 4. Get current user
curl http://localhost:5000/api/auth/me \
  -b cookies.txt
```

### Test With Automation
```bash
# Run all tests automatically
./test_api.sh
```

---

## 🐛 Common Mistakes

### ❌ Mistake 1: Not including credentials
```javascript
// WRONG - cookies not sent
fetch('http://localhost:5000/api/profile')

// CORRECT - cookies sent
fetch('http://localhost:5000/api/profile', {
  credentials: 'include'
})
```

### ❌ Mistake 2: Wrong endpoint
```javascript
// WRONG
'/profile'

// CORRECT
'/api/profile'
```

### ❌ Mistake 3: Not handling errors
```javascript
// WRONG
const user = await fetch(...).json();

// CORRECT
const response = await fetch(...);
if (!response.ok) {
  const error = await response.json();
  throw new Error(error.error);
}
const user = await response.json();
```

### ❌ Mistake 4: Using wrong HTTP method
```javascript
// WRONG - GET for sending data
fetch('/chat/send', { 
  method: 'GET',
  body: JSON.stringify(data)
})

// CORRECT - POST for sending data
fetch('/chat/send', { 
  method: 'POST',
  body: JSON.stringify(data)
})
```

---

## 📖 Documentation Structure

### For Quick Reference
1. **This file** - Start here!
2. **REST_API_DOCUMENTATION.md** - Detailed endpoint docs
3. **test_api.sh** - Test all endpoints

### For Implementation
1. **FRONTEND_INTEGRATION_GUIDE.md** - Step-by-step guide
2. **API endpoint examples** - Copy-paste ready code
3. **Custom hooks** - React hooks for API calls

---

## 🎯 Next Steps

### For Frontend Developers
1. ✅ Read `REST_API_DOCUMENTATION.md`
2. ✅ Run `./test_api.sh` to verify backend
3. ✅ Follow `FRONTEND_INTEGRATION_GUIDE.md`
4. ✅ Implement authentication
5. ✅ Implement conversations
6. ✅ Implement chat
7. ✅ Implement profile
8. ✅ Add error handling
9. ✅ Test everything

### For Backend Developers
1. ✅ Verify all endpoints are implemented
2. ✅ Run tests with `./test_api.sh`
3. ✅ Check response formats match docs
4. ✅ Fix any errors immediately

---

## 🔗 File Locations

All documentation is in the project root:
```
medical-chatbot/
├── REST_API_DOCUMENTATION.md          ← Main API reference
├── FRONTEND_INTEGRATION_GUIDE.md       ← Integration guide
├── test_api.sh                         ← Testing script
└── python_backend/                    ← Backend code
    ├── app.py                         ← Main app
    └── routes/                        ← All endpoints
```

---

## 💬 Questions?

### If endpoint doesn't work
1. Check backend is running: `curl http://localhost:5000/api/health`
2. Check method is correct (GET, POST, PUT, DELETE)
3. Check you sent all required fields
4. Check cookies are included with `credentials: 'include'`
5. Look at console output for errors

### If you need help
1. **Read the detailed docs** - Most questions answered there
2. **Look at CURL examples** - See exactly how endpoint works
3. **Check error messages** - Backend returns helpful error text
4. **Run test script** - See if endpoint works at all

---

## 🚀 You're Ready!

Everything you need to integrate the frontend with the backend is documented here.

**Start with REST_API_DOCUMENTATION.md for detailed explanations with examples!**

Good luck! 🎉
