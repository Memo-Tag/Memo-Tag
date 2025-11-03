#!/bin/bash

# MedChat REST API Testing Script
# Run all API endpoints with CURL to verify they work
# Usage: bash test_api.sh

# Don't exit on error - we want to continue testing even if one fails
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:5000/api"
COOKIES_FILE="cookies.txt"

# Cleanup old cookies
rm -f $COOKIES_FILE

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    MedChat REST API Testing Script                        ║${NC}"
echo -e "${BLUE}║    Testing all endpoints with CURL                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Function to test endpoint
test_endpoint() {
  local test_name=$1
  local method=$2
  local endpoint=$3
  local data=$4
  local expected_code=$5
  
  echo -e "\n${YELLOW}[TEST] ${test_name}${NC}"
  echo -e "  Method: $method | Endpoint: $endpoint"
  
  # Run curl and capture both output and status code
  local response
  local curl_exit_code
  
  if [ -z "$data" ]; then
    response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" \
      -H "Content-Type: application/json" \
      -b $COOKIES_FILE -c $COOKIES_FILE 2>&1)
    curl_exit_code=$?
  else
    response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" \
      -H "Content-Type: application/json" \
      -d "$data" \
      -b $COOKIES_FILE -c $COOKIES_FILE 2>&1)
    curl_exit_code=$?
  fi
  
  # Check if curl itself failed
  if [ $curl_exit_code -ne 0 ]; then
    echo -e "  ${RED}❌ CURL ERROR (exit code: $curl_exit_code)${NC}"
    echo -e "  Response: $response"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
  
  # Extract status code (last line)
  local status_code=$(echo "$response" | tail -1)
  # Extract body (everything except last line)
  local body=$(echo "$response" | head -n-1)
  
  echo -e "  Response Code: $status_code"
  
  if [ "$status_code" = "$expected_code" ]; then
    echo -e "  ${GREEN}✅ PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Pretty print JSON response (if available)
    if command -v jq &> /dev/null; then
      echo -e "  ${GREEN}Response:${NC}"
      echo "$body" | jq '.' 2>/dev/null | sed 's/^/    /' || echo "$body" | sed 's/^/    /'
    else
      echo -e "  Response: $body"
    fi
  else
    echo -e "  ${RED}❌ FAILED (Expected $expected_code, got $status_code)${NC}"
    echo -e "  Response: $body"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
}

# ============================================
# 1. HEALTH CHECK
# ============================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}1. HEALTH CHECK${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

test_endpoint "Health Check" "GET" "/health" "" "200"

# ============================================
# 2. AUTHENTICATION - EMAIL/PASSWORD
# ============================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}2. AUTHENTICATION - EMAIL/PASSWORD${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Register
TEST_EMAIL="testuser_$(date +%s)@medchat.com"
TEST_PASSWORD="SecurePassword123!"
TEST_NAME="Test User $(date +%s)"

REGISTER_DATA="{\"name\":\"$TEST_NAME\",\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}"
test_endpoint "User Registration (Sign Up)" "POST" "/auth/register" "$REGISTER_DATA" "201"

# Extract user ID from response
USER_ID=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Test User\",\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
  -b $COOKIES_FILE -c $COOKIES_FILE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

# Login
LOGIN_DATA="{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}"
test_endpoint "User Login (Email/Password)" "POST" "/auth/login" "$LOGIN_DATA" "200"

# Get current user
test_endpoint "Get Current User Info" "GET" "/auth/me" "" "200"

# ============================================
# 3. CONVERSATIONS
# ============================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}3. CONVERSATIONS${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Create conversation
CONV_DATA="{\"title\":\"Test Conversation\"}"

# Make the request and capture response for ID extraction
CONV_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/conversations" \
  -H "Content-Type: application/json" \
  -d "$CONV_DATA" \
  -b $COOKIES_FILE -c $COOKIES_FILE)

# Extract status code and body
CONV_STATUS=$(echo "$CONV_RESPONSE" | tail -1)
CONV_BODY=$(echo "$CONV_RESPONSE" | head -n-1)

# Test the endpoint
echo -e "\n${YELLOW}[TEST] Create New Conversation${NC}"
echo -e "  Method: POST | Endpoint: /conversations"
echo -e "  Response Code: $CONV_STATUS"

if [ "$CONV_STATUS" = "201" ]; then
  echo -e "  ${GREEN}✅ PASSED${NC}"
  TESTS_PASSED=$((TESTS_PASSED + 1))
  echo -e "  ${GREEN}Response:${NC}"
  echo "$CONV_BODY" | sed 's/^/    /'
else
  echo -e "  ${RED}❌ FAILED (Expected 201, got $CONV_STATUS)${NC}"
  echo -e "  Response: $CONV_BODY"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Extract conversation ID from response using Python for reliability
CONVERSATION_ID=$(echo "$CONV_BODY" | python -c "import sys, json; data = json.load(sys.stdin); print(data.get('conversation', {}).get('id', ''))" 2>/dev/null || echo "")

# Fallback to grep if Python not available
if [ -z "$CONVERSATION_ID" ]; then
  CONVERSATION_ID=$(echo "$CONV_BODY" | grep -oP '(?<="id":")[a-zA-Z0-9_]+(?=")' | head -1)
fi

# Last fallback to basic sed
if [ -z "$CONVERSATION_ID" ]; then
  CONVERSATION_ID=$(echo "$CONV_BODY" | sed -n 's/.*"id":"\(conv_[^"]*\)".*/\1/p')
fi

echo -e "  ${GREEN}Extracted Conversation ID: '$CONVERSATION_ID'${NC}"

if [ -z "$CONVERSATION_ID" ] || [ "$CONVERSATION_ID" = "null" ]; then
  echo -e "  ${RED}⚠️  WARNING: Could not extract ID. Response was:${NC}"
  echo "$CONV_BODY"
fi

# List conversations
test_endpoint "List All Conversations" "GET" "/conversations" "" "200"

# Get specific conversation
if [ -z "$CONVERSATION_ID" ] || [ "$CONVERSATION_ID" = "null" ]; then
  echo -e "\n${YELLOW}[SKIP] Get Conversation with Messages${NC}"
  echo -e "  ${RED}Cannot test - Conversation ID not available${NC}"
  TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
else
  test_endpoint "Get Conversation with Messages" "GET" "/conversations/$CONVERSATION_ID" "" "200"
fi

# Update conversation title
if [ -z "$CONVERSATION_ID" ] || [ "$CONVERSATION_ID" = "null" ]; then
  echo -e "\n${YELLOW}[SKIP] Update Conversation Title${NC}"
  echo -e "  ${RED}Cannot test - Conversation ID not available${NC}"
  TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
else
  UPDATE_DATA="{\"title\":\"Updated: Test Conversation\"}"
  test_endpoint "Update Conversation Title" "PUT" "/conversations/$CONVERSATION_ID" "$UPDATE_DATA" "200"
fi

# ============================================
# 4. CHAT
# ============================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}4. CHAT (AI RESPONSES)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Get available models
test_endpoint "Get Available AI Models" "GET" "/chat/models" "" "200"

# Send message
if [ -z "$CONVERSATION_ID" ] || [ "$CONVERSATION_ID" = "null" ]; then
  echo -e "\n${YELLOW}[SKIP] Send Message (Get AI Response)${NC}"
  echo -e "  ${RED}Cannot test - Conversation ID not available${NC}"
  TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
else
  CHAT_DATA="{\"conversationId\":\"$CONVERSATION_ID\",\"message\":\"What are the symptoms of diabetes?\",\"model\":\"sonar\"}"
  test_endpoint "Send Message (Get AI Response)" "POST" "/chat/send" "$CHAT_DATA" "200"
fi

# ============================================
# 5. PROFILE
# ============================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}5. PROFILE${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Get profile
test_endpoint "Get User Profile" "GET" "/profile" "" "200"

# Update profile
PROFILE_DATA="{\"phone\":\"+1 (555) 123-4567\",\"dateOfBirth\":\"1990-01-15\",\"bio\":\"Test user\"}"
test_endpoint "Update User Profile" "PUT" "/profile" "$PROFILE_DATA" "200"

# ============================================
# 6. PREFERENCES
# ============================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}6. PREFERENCES${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Get preferences
test_endpoint "Get User Preferences" "GET" "/preferences" "" "200"

# Update preferences
PREF_DATA="{\"preferredModel\":\"sonar\",\"ageGroup\":\"young\",\"responseStyle\":\"simple\"}"
test_endpoint "Update User Preferences" "PUT" "/preferences" "$PREF_DATA" "200"

# ============================================
# 7. PATIENT MEMORY
# ============================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}7. PATIENT MEMORY${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Get patient memory
test_endpoint "Get Patient Memory" "GET" "/memory/patient" "" "200"

# ============================================
# 8. AUTHENTICATION - LOGOUT
# ============================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}8. LOGOUT${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

test_endpoint "User Logout" "POST" "/auth/logout" "" "200"

# ============================================
# 9. CLEANUP - DELETE CONVERSATION
# ============================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}9. CLEANUP${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Need to login again to delete
LOGIN_DATA="{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}"
curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_DATA" \
  -b $COOKIES_FILE -c $COOKIES_FILE > /dev/null

if [ -z "$CONVERSATION_ID" ] || [ "$CONVERSATION_ID" = "null" ]; then
  echo -e "\n${YELLOW}[SKIP] Delete Conversation${NC}"
  echo -e "  ${RED}Cannot test - Conversation ID not available${NC}"
  TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
else
  test_endpoint "Delete Conversation" "DELETE" "/conversations/$CONVERSATION_ID" "" "200"
fi

# ============================================
# SUMMARY
# ============================================
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))
if [ $TOTAL_TESTS -gt 0 ]; then
  PASS_PERCENTAGE=$((TESTS_PASSED * 100 / (TESTS_PASSED + TESTS_FAILED)))
else
  PASS_PERCENTAGE=0
fi

echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED ✅${NC}"
echo -e "${RED}Failed: $TESTS_FAILED ❌${NC}"
echo -e "${YELLOW}Skipped: $TESTS_SKIPPED ⏭️${NC}"
if [ $TESTS_FAILED -gt 0 ] || [ $TESTS_SKIPPED -gt 0 ]; then
  echo -e "Pass Rate: ${PASS_PERCENTAGE}% (excluding skipped)"
else
  echo -e "Pass Rate: ${PASS_PERCENTAGE}%"
fi

if [ $TESTS_FAILED -eq 0 ]; then
  if [ $TESTS_SKIPPED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! API is working correctly!${NC}"
  else
    echo -e "\n${GREEN}✅ All executable tests passed! ($TESTS_SKIPPED skipped due to missing prerequisites)${NC}"
  fi
  exit 0
else
  echo -e "\n${RED}❌ Some tests failed. Check the output above.${NC}"
  exit 1
fi
