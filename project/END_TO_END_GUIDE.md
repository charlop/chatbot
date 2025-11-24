# End-to-End Testing Guide
## Contract Refund Eligibility System - Complete User Flow

**Last Updated:** November 16, 2025
**Status:** ✅ Ready for end-to-end testing

---

## 🚀 Quick Start

```bash
# From project root
cd /Users/chris/dev/chatbot/project

# Start all services (PostgreSQL, Redis, Backend, Frontend)
./start.sh --seed

# Services will be available at:
# - Frontend:  http://localhost:3000
# - Backend:   http://localhost:8001
# - API Docs:  http://localhost:8001/docs
```

**That's it!** The system is now running with test data.

---

## 📋 Prerequisites

Before running the system, ensure you have:

- ✅ **Docker Desktop** - For PostgreSQL and Redis
- ✅ **UV** - Python package manager for backend
- ✅ **Node.js & npm** - For frontend (v18 or higher)
- ✅ **netcat (nc)** - For health checks (optional)

All checks are performed automatically by `start.sh`.

---

## 🎯 Complete End-to-End User Flow

### Step 1: Start the System

```bash
# From project root
./start.sh --seed
```

Expected output:
```
================================
Contract Refund Eligibility System
================================
Starting all services...

✅ All prerequisites met

================================
Step 1: Starting Docker Services
================================
✅ PostgreSQL is ready
✅ Redis is ready

================================
Step 2: Seeding Database
================================
✅ Database seeded successfully

================================
Step 3: Starting Backend API
================================
✅ Backend API started successfully
   📚 API Docs: http://localhost:8001/docs

================================
Step 4: Starting Frontend
================================
✅ Frontend started successfully
   🌐 Web UI: http://localhost:3000

✅ All Services Started
```

### Step 2: Access the Application

1. Open your browser to **http://localhost:3000**
2. You'll see the **Dashboard** page

### Step 3: Search for a Contract

**Test Account Numbers** (from seed data):
```
ACC-TEST-00001
ACC-TEST-00002
ACC-TEST-00003
```

1. **Enter account number** in the search bar: `ACC-TEST-00001`
2. **Click "Search"** button
3. **View search results** - Should show contract details
4. **Click "View Details"** button

### Step 4: View Contract Details

You should now see the **Contract Details Page** with:

**✅ Left Panel (PDF Viewer):**
- Contract PDF displayed
- Zoom controls (50%, 100%, 150%, 200%, Fit)
- Page navigation
- Download button

**✅ Right Panel (Extracted Data or Trigger):**

**If extraction hasn't run:**
- Contract information (customer, vehicle, metadata)
- "Start Extraction" button

**If extraction has run:**
- GAP Insurance Premium with confidence badge
- Refund Calculation Method with confidence badge
- Cancellation Fee with confidence badge
- Source locations for each field
- "Submit" button

**✅ Bottom Right (Collapsible Chat):**
- Chat interface (collapsed by default)
- Shows account number and contract ID in header
- Click "Expand ↑" to open chat

### Step 5: Extract Data (if needed)

1. **Click "Start Extraction"** button
2. **Wait 2-5 seconds** for AI to extract data
3. **View extracted fields** with confidence scores:
   - Green badge (>90%): High confidence
   - Orange badge (70-90%): Medium confidence
   - Red badge (<70%): Low confidence

### Step 6: Review and Approve/Edit

**Option A: Approve as-is**
1. **Review extracted values** against the PDF
2. **Click "Submit"** button
3. **Confirm submission** in modal
4. **Success!** - Contract is marked as approved

**Option B: Make corrections**
1. **Click on a field value** to edit inline
2. **Type corrected value**
3. **Press Enter** or click outside to save edit
4. Field shows "Edited" indicator
5. **Click "Submit"** button
6. **Review corrections summary** in modal
7. **Optionally add notes** about why you made corrections
8. **Confirm submission**
9. **Success!** - Contract is approved with corrections

### Step 7: Use the Chat Interface

1. **Click "Expand ↑"** button in bottom right
2. **Chat panel expands** to 400px height
3. **Type a question** about the contract:
   ```
   What is the GAP Insurance Premium?
   What refund method does this contract use?
   Are there any cancellation fees?
   ```
4. **Press Enter** or click "Send"
5. **AI responds** with answer based on contract content
6. **Ask follow-up questions** - conversation history maintained
7. **Click "Collapse ↓"** to minimize chat (input text preserved)

**Keyboard Shortcut:** Press `Ctrl+`` (or `Cmd+`` on Mac) to toggle chat

### Step 8: Navigate Back

1. **Click "Back to Dashboard"** button
2. **Return to search page**
3. **Recent searches** shows your previous search
4. **Click recent search** to quickly re-search

---

## 🧪 Test Scenarios

### Scenario 1: Happy Path (High Confidence)

```
Account: ACC-TEST-00001
Expected: High confidence scores (>90%) for all fields
Flow: Search → View → Extract → Review → Approve
```

### Scenario 2: Corrections Required (Low Confidence)

```
Account: ACC-TEST-00002
Expected: Some low confidence scores (<70%)
Flow: Search → View → Extract → Edit fields → Submit with corrections
```

### Scenario 3: Chat Questions

```
Account: ACC-TEST-00001
Test Questions:
- "What is the cancellation fee?"
- "How is the refund calculated?"
- "What is covered under GAP insurance?"
```

### Scenario 4: Multiple Contracts

```
Search: ACC-TEST-00001 → View → Back
Search: ACC-TEST-00002 → View → Compare
```

### Scenario 5: PDF Navigation

```
1. Click "View in document" on a data field
2. PDF should jump to the source page
3. Relevant section should be highlighted (if implemented)
```

---

## 🔍 Testing Checklist

### Frontend Tests

- [ ] **Dashboard loads** successfully
- [ ] **Search bar** accepts input
- [ ] **Search results** display correctly
- [ ] **Contract details page** loads
- [ ] **PDF viewer** displays PDF
- [ ] **Zoom controls** work (50%, 100%, 150%, 200%)
- [ ] **Page navigation** works (prev/next)
- [ ] **Data extraction** triggers successfully
- [ ] **Extracted data** displays with confidence badges
- [ ] **Inline editing** works (click field, edit, save)
- [ ] **Submit button** submits data
- [ ] **Audit trail** shows processing info
- [ ] **Chat expands/collapses** smoothly
- [ ] **Chat messages** send and receive
- [ ] **Keyboard shortcut** (Ctrl+`) toggles chat
- [ ] **Back navigation** returns to dashboard
- [ ] **Recent searches** persist

### Backend Tests

```bash
# Health check
curl http://localhost:8001/health

# Search for contract
curl -X POST http://localhost:8001/api/v1/contracts/search \
  -H 'Content-Type: application/json' \
  -d '{"account_number": "ACC-TEST-00001"}'

# Get contract
curl http://localhost:8001/api/v1/contracts/{contractId}

# Trigger extraction
curl -X POST http://localhost:8001/api/v1/extractions \
  -H 'Content-Type: application/json' \
  -d '{"contractId": "{contractId}"}'

# Submit extraction
curl -X POST http://localhost:8001/api/v1/extractions/{extractionId}/submit \
  -H 'Content-Type: application/json' \
  -d '{"corrections": [], "notes": "Approved"}'

# Chat
curl -X POST http://localhost:8001/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"contractId": "{contractId}", "message": "What is the GAP premium?", "history": []}'
```

### Integration Tests

- [ ] **Search → View** navigation works
- [ ] **Extract → Display** data flow works
- [ ] **Edit → Submit** saves corrections
- [ ] **Chat → API** communication works
- [ ] **PDF → Data** linking works (View in document)
- [ ] **Error handling** shows user-friendly messages
- [ ] **Loading states** display during async operations

---

## 📊 Expected Test Data

The `--seed` flag creates:

**3 Test Contracts:**
```
ACC-TEST-00001 - John Smith - 2015 Toyota Camry
ACC-TEST-00002 - Jane Doe - 2018 Honda Accord
ACC-TEST-00003 - Bob Johnson - 2020 Ford F-150
```

**Sample Extraction Data:**
```
GAP Premium: $1,250.00 - $1,500.00
Refund Method: Pro-Rata, Rule of 78s, etc.
Cancellation Fee: $50.00 - $100.00
```

---

## 🛑 Stopping Services

### Quick Stop (All Services)

```bash
# Kill backend and frontend
kill $(cat /tmp/project_pids.txt | grep PID | cut -d= -f2)

# Stop Docker services
cd backend && docker-compose down
```

### Manual Stop

```bash
# Stop backend
lsof -ti:8001 | xargs kill

# Stop frontend
lsof -ti:3000 | xargs kill

# Stop Docker
cd backend && docker-compose down
```

---

## 📝 Logs & Debugging

### View Logs

```bash
# Backend logs
tail -f /tmp/backend.log

# Frontend logs
tail -f /tmp/frontend.log

# Docker logs
cd backend && docker-compose logs -f

# PostgreSQL logs
cd backend && docker-compose logs -f postgres

# Redis logs
cd backend && docker-compose logs -f redis
```

### Check Service Status

```bash
# Check if services are running
lsof -i:3000  # Frontend
lsof -i:8001  # Backend
lsof -i:5432  # PostgreSQL
lsof -i:6379  # Redis

# Check Docker containers
cd backend && docker-compose ps
```

### Common Issues

**Issue: Port already in use**
```bash
# Kill process on port
lsof -ti:8001 | xargs kill  # Backend
lsof -ti:3000 | xargs kill  # Frontend
```

**Issue: Database connection failed**
```bash
# Restart Docker services
cd backend && docker-compose restart
```

**Issue: Frontend won't start**
```bash
# Reinstall dependencies
cd frontend && rm -rf node_modules && npm install
```

**Issue: Backend extraction fails**
```bash
# Check if LLM API keys are configured
cat backend/.env | grep -E "OPENAI|ANTHROPIC|AWS"
```

---

## 🎯 Success Criteria

The system is working correctly if you can:

1. ✅ **Search** for a contract by account number
2. ✅ **View** contract details with PDF
3. ✅ **Extract** data using AI
4. ✅ **Review** extracted data with confidence scores
5. ✅ **Edit** incorrect values inline
6. ✅ **Submit** approved/corrected data
7. ✅ **Chat** with AI about the contract
8. ✅ **Navigate** between contracts smoothly
9. ✅ **View** audit trail with processing info
10. ✅ **Use** keyboard shortcuts (Ctrl+` for chat)

---

## 🔗 API Documentation

**Interactive API Docs:**
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

**Key Endpoints:**
```
POST   /api/v1/contracts/search
GET    /api/v1/contracts/{contractId}
POST   /api/v1/extractions
GET    /api/v1/extractions/{extractionId}
POST   /api/v1/extractions/{extractionId}/submit
POST   /api/v1/chat
GET    /health
```

---

## 📈 Performance Expectations

| Operation | Target Time | Measured |
|-----------|-------------|----------|
| Search contract | < 3 seconds | TBD |
| Load contract page | < 2 seconds | TBD |
| AI extraction | < 10 seconds | TBD |
| PDF load | < 2 seconds | TBD |
| Chat response | < 5 seconds | TBD |
| Submit approval | < 1 second | TBD |

---

## ✅ Ready for Production?

**Checklist:**
- [ ] All integration tests passing
- [ ] End-to-end user flow works smoothly
- [ ] Error handling covers edge cases
- [ ] Loading states display correctly
- [ ] Chat provides helpful responses
- [ ] Performance meets targets
- [ ] Security audit completed (deferred)
- [ ] User acceptance testing (UAT) passed (deferred)

**MVP Status:** ✅ **READY FOR DEMO**
**Production Status:** ⚠️ **Requires security audit and UAT**

---

## 🚀 Next Steps

1. **Demo the system** to stakeholders
2. **Gather feedback** from finance users
3. **Security audit** (authentication, authorization, data encryption)
4. **Performance optimization** (caching, query optimization)
5. **Production deployment** (AWS infrastructure setup)
6. **User training** (1-hour training session)
7. **Monitor usage** (analytics, error tracking)

---

**Questions or Issues?**
- Check logs: `tail -f /tmp/backend.log` and `tail -f /tmp/frontend.log`
- Review API docs: http://localhost:8001/docs
- Check database: `docker exec -it backend-postgres psql -U contract_user -d contract_refund_db`

**Happy Testing! 🎉**
