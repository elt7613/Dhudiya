USER AUTHENTICATION SYSTEM TEST DOCUMENTATION
==========================================

1. OVERVIEW
-----------
This document describes the test suite for the user authentication system. The tests are organized into three main classes:
- UserModelTests: Tests for the User model
- UserAPITests: Tests for API endpoints
- UserAuthenticationTests: Tests for JWT authentication

2. TEST CLASSES
--------------

2.1 UserModelTests
-----------------
Purpose: Tests the User model functionality and properties

Setup:
- Creates a test user with username, phone number, email, and password
- Executed before each test method

Test Methods:
a) test_create_user
   - Verifies user creation with correct attributes
   - Checks username, phone number, email match
   - Validates password hashing
   - Confirms default permissions (is_active, is_staff, is_superuser)

b) test_user_str_method
   - Validates string representation of user object
   - Ensures it returns username

2.2 UserAPITests
---------------
Purpose: Tests API endpoints for registration and login

Setup:
- Initializes test URLs using reverse()
- Creates test user data
- Clears cache before each test

Test Methods:
a) test_user_registration
   - Tests successful user registration
   - Validates response status (201 Created)
   - Checks token generation
   - Verifies user creation in database

b) test_duplicate_username_registration
   - Tests duplicate username handling
   - Expects 400 Bad Request
   - Verifies error message

c) test_login_with_username
   - Tests login using username
   - Validates successful login response
   - Checks token presence

d) test_login_with_phone
   - Tests login using phone number
   - Validates successful login response
   - Checks token presence

e) test_login_with_wrong_password
   - Tests failed login attempt
   - Expects 401 Unauthorized

f) test_login_attempt_limit
   - Tests rate limiting after failed attempts
   - Makes 5 failed attempts
   - Verifies lockout on 6th attempt
   - Expects 429 Too Many Requests

g) test_registration_with_invalid_phone
   - Tests phone number validation
   - Uses invalid phone format
   - Expects 400 Bad Request

h) test_registration_without_required_fields
   - Tests missing required fields
   - Expects 400 Bad Request

i) test_rate_limiting
   - Tests API rate limiting
   - Makes 21 requests (limit is 20/minute)
   - Expects 429 Too Many Requests

2.3 UserAuthenticationTests
--------------------------
Purpose: Tests JWT token authentication

Setup:
- Creates test user
- Generates JWT token

Test Methods:
a) test_authentication_with_valid_token
   - Tests valid token authentication
   - Sets Authorization header
   - Template for protected endpoint testing

b) test_authentication_without_token
   - Tests unauthorized access
   - Template for protected endpoint testing

c) test_authentication_with_invalid_token
   - Tests invalid token handling
   - Template for protected endpoint testing

3. RUNNING THE TESTS
-------------------
Command: python manage.py test user.tests

Expected Output:
- All tests should pass
- Coverage of core functionality
- Clear error messages for failures

4. TEST DEPENDENCIES
-------------------
- Django Test Framework
- Django REST Framework APITestCase
- JWT Token functionality
- Redis for caching tests

5. TESTING CONSIDERATIONS
------------------------
1. Database:
   - Tests use separate test database
   - Database is created/destroyed for each test
   - Isolated from production data

2. Cache:
   - Cache is cleared before each test
   - Prevents test interference

3. Rate Limiting:
   - Tests both endpoint-specific limits
   - Tests global rate limiting

4. Authentication:
   - Tests both username and phone number login
   - Validates token generation and validation
   - Tests security measures

6. EXTENDING THE TESTS
---------------------
To add new tests:
1. Choose appropriate test class
2. Follow existing pattern for setup
3. Add new test methods
4. Document purpose and expectations
5. Ensure isolation from other tests

7. PROTECTED ENDPOINT TESTING
---------------------------
Currently commented sections available for:
- Valid token access
- Missing token access
- Invalid token access

To implement:
1. Uncomment relevant sections
2. Add your protected endpoint URL
3. Add specific assertions for your endpoint

8. MAINTENANCE
-------------
Regular updates needed for:
- New features
- Security changes
- API modifications
- Dependency updates

9. TROUBLESHOOTING
-----------------
Common issues:
1. Rate limit failures
   - Check Redis connection
   - Verify throttle settings

2. Authentication failures
   - Check token configuration
   - Verify user creation

3. Database errors
   - Check migrations
   - Verify test database settings
