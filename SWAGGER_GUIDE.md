# 📚 Gawa API - Swagger/OpenAPI Documentation Guide

Complete guide to testing Gawa APIs using interactive Swagger documentation.

---

## 🎯 Quick Start

Once the server is running, access the documentation at:

### **Swagger UI** (Interactive Testing)
```
http://localhost:8000/api/docs/
```

### **ReDoc** (Beautiful Documentation)
```
http://localhost:8000/api/redoc/
```

### **OpenAPI Schema** (Raw Schema)
```
http://localhost:8000/api/schema/
```

---

## 🚀 Getting Started

### 1. Start the Development Server

```bash
cd C:\Users\Mokaya\Downloads\GitHub\Gawa
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

### 2. Open Swagger UI

Navigate to: **http://localhost:8000/api/docs/**

You should see a beautiful interactive API documentation interface!

---

## 🔑 Authentication in Swagger

### Step 1: Get Access Token

1. Scroll to the **auth** section
2. Click on **POST /api/auth/login/**
3. Click the **"Try it out"** button
4. Enter your credentials:
   ```json
   {
     "email": "your-email@example.com",
     "password": "your-password"
   }
   ```
5. Click **Execute**
6. Copy the `access_token` from the response

### Step 2: Set Authorization Header

1. Click the **green "Authorize"** button at the top
2. Paste your token in the format:
   ```
   Bearer your_access_token_here
   ```
3. Click **Authorize**
4. Click **Close**

Now all your requests will include the authorization header!

---

## 🧪 Testing API Endpoints

### Example 1: Create a Group

1. Navigate to **groups** section
2. Find **POST /api/groups/**
3. Click **"Try it out"**
4. Fill in the request body:
   ```json
   {
     "title": "Weekend Trip",
     "description": "Beach vacation",
     "member_phone_numbers": ["+254712345678"]
   }
   ```
5. Click **Execute**
6. See the response with your new group!

### Example 2: Create an Expense

1. Navigate to **expenses** section
2. Find **POST /api/expenses/**
3. Click **"Try it out"**
4. Fill in the request body:
   ```json
   {
     "group_id": 1,
     "title": "Dinner",
     "total_amount": 2000,
     "split_type": "equal",
     "participant_ids": ["user-1", "user-2"],
     "description": "Restaurant bill"
   }
   ```
5. Click **Execute**

### Example 3: Initiate Payment

1. Navigate to **payments** section
2. Find **POST /api/payments/initiate/**
3. Click **"Try it out"**
4. Fill in:
   ```json
   {
     "expense_id": 1,
     "participant_id": "user-1"
   }
   ```
5. Click **Execute**

---

## 📊 API Sections in Swagger

### **auth**
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login & get token

### **users**
- `GET /api/users/me/` - Get your profile
- `GET/PUT /api/users/profile/` - View/update profile

### **groups**
- `GET /api/groups/` - List your groups
- `POST /api/groups/` - Create new group
- `GET /api/groups/{id}/` - Get group details
- `POST /api/groups/{id}/add_member/` - Add member
- `GET /api/groups/{id}/balances/` - View balances

### **expenses**
- `GET /api/expenses/` - List expenses
- `POST /api/expenses/` - Create expense
- `GET /api/expenses/{id}/` - Get details
- `POST /api/expenses/{id}/settle/` - Mark settled

### **payments**
- `GET /api/payments/` - List payments
- `POST /api/payments/initiate/` - Start payment
- `GET /api/payments/{id}/status/` - Check status

### **ai**
- `POST /api/ai/smart-split/` - Generate suggestions

---

## 🎨 Features of Swagger UI

### 📝 Request Input
- Automatic input validation
- Type hints for each field
- Required field indicators
- Example values

### 📤 Response Display
- Pretty-printed JSON
- Response status codes
- Response headers
- Execution time

### 🔍 Schema Information
- Data type descriptions
- Field requirements
- Example values
- Default values

### 💾 Copy/Paste
- Copy as cURL
- Copy response
- Easy code generation

---

## 🔄 Common Workflows

### Workflow 1: Create Group → Add Expense → Initiate Payment

```
1. Register user (if needed)
   POST /api/auth/register/

2. Login to get token
   POST /api/auth/login/

3. Create group
   POST /api/groups/

4. Create expense
   POST /api/expenses/

5. Initiate payment
   POST /api/payments/initiate/

6. Check payment status
   GET /api/payments/{id}/status/
```

### Workflow 2: View Balances

```
1. Get your profile
   GET /api/users/me/

2. List groups
   GET /api/groups/

3. View group balances
   GET /api/groups/{id}/balances/
```

---

## 🐛 Debugging Tips

### View Request Details
- Click **"Request body"** to see what was sent
- Check **"Response headers"** for metadata
- Look at **"Response body"** for errors

### Common Errors

**401 Unauthorized**
- Your token is missing or invalid
- Click the green "Authorize" button again
- Make sure you prefixed with "Bearer "

**404 Not Found**
- The resource doesn't exist
- Check the ID is correct
- Make sure you created it first

**400 Bad Request**
- Check your request body format
- Verify all required fields are provided
- Look at error message for details

**422 Unprocessable Entity**
- Validation error in your data
- Check data types (string, number, etc.)
- Verify relationships exist

---

## 📋 Response Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK - Success | GET request successful |
| 201 | Created - Resource created | POST created new expense |
| 400 | Bad Request - Invalid data | Wrong data format |
| 401 | Unauthorized - Need login | Missing/invalid token |
| 403 | Forbidden - No permission | Accessing someone else's data |
| 404 | Not Found - Doesn't exist | Group ID doesn't exist |
| 500 | Server Error | Backend issue |

---

## 🔐 Security Notes

### Authorization
- Your token is stored **locally in browser**
- Never share your token
- Use "Authorize" button for temporary session
- Session ends when you close the browser (in dev mode)

### Password
- Never enter real passwords in Swagger (dev only)
- Use test credentials for development
- In production, use separate auth process

---

## 💻 Advanced Testing

### Download OpenAPI Schema
1. Visit: `http://localhost:8000/api/schema/`
2. Right-click → Save page as
3. Import into Postman or Insomnia

### Generate Client Code
Many tools can generate client libraries from OpenAPI schema:
- Postman can import and use the schema
- OpenAPI generators create SDKs
- IDE tools can generate types

### Bulk Testing
1. Export requests from Swagger
2. Use Postman collection runner
3. Automate testing workflows

---

## 🎓 Learning Resources

### From Swagger UI
- Hover over fields for descriptions
- Click **"Schema"** tab to see data structure
- Check **"Example Value"** for sample data

### From Response
- Every response shows actual data structure
- Status codes explain what happened
- Error messages explain what went wrong

---

## ✨ Pro Tips

1. **Use Authorization Button**
   - Set once, applies to all requests
   - No need to manually add header

2. **Copy cURL Commands**
   - Right-click any request section
   - Use in terminal for scripting

3. **Try Different Scenarios**
   - Valid data → should succeed
   - Invalid data → should show error
   - Missing required fields → should fail

4. **Check Example Values**
   - Click on field to see examples
   - Great for understanding format

5. **Use ReDoc for Reading**
   - Better for documentation
   - Better for API exploration
   - Use Swagger for testing

---

## 🔗 Access Points

| URL | Purpose | Best For |
|-----|---------|----------|
| `/api/docs/` | Swagger UI | Interactive testing |
| `/api/redoc/` | ReDoc | Reading documentation |
| `/api/schema/` | OpenAPI JSON | Integration tools |
| `/api/` | API Root | Browsable API (optional) |

---

## 🆘 Troubleshooting

### Swagger Not Loading
- Make sure server is running
- Check URL is correct
- Clear browser cache (Ctrl+Shift+Delete)
- Try different browser

### Authorization Not Working
- Check Bearer token format
- Make sure token is still valid
- Try logging in again

### Endpoint Not Showing
- Refresh the page
- Check if app is installed in settings.py
- Verify URL routing is correct

### Response Shows Error
- Read the error message
- Check the HTTP status code
- Verify your data is correct

---

## 📞 Need Help?

1. Check error response message
2. Review this guide
3. Check API documentation in README.md
4. Review code comments in views.py
5. Check test examples in tests.py

---

## 🎉 You're Ready!

You now have a powerful, interactive API testing tool at your fingertips!

**Start testing: http://localhost:8000/api/docs/**

---

**Happy API Testing! 🚀**
