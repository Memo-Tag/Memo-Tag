File	                            Size	Purpose
START_HERE.txt	                    10.5 KB	Visual overview & quick start guide
API_QUICK_SUMMARY.md	             8.5 KB	Quick reference for all endpoints
REST_API_DOCUMENTATION.md	    31.5 KB	Complete detailed reference for all 19 endpoints
FRONTEND_INTEGRATION_GUIDE.md	    20.1 KB	Step-by-step implementation guide with React hooks
test_api.sh	                    11.4 KB	Automated CURL testing script for all endpoints





What it's testing:
Group	                          Endpoints	What it does
Health	                               1	Check if backend is alive
Auth	                               5	Register, Login, Get User, Logout, Google OAuth
Conversations	                       5	Create, List, Get, Update, Delete
Chat	                               2	Send Message, Get Models
Profile	                               2	Get, Update
Preferences	                       2	Get, Update
Memory	                               1	Get Patient Memory



How to use it:
bash
# 1. Make sure backend is running on port 5000
	cd python_backend
	python app.py

# 2. In another terminal, run the test script
	cd medical_chatbot
	bash test_api.sh
	What you see:
The script shows:
✅ Which tests PASSED (green)
❌ Which tests FAILED (red)
⏭️ Which tests were SKIPPED (yellow - if dependencies missing)
Final pass rate and summary
