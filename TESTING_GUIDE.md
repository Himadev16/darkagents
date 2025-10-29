# 🧪 DARKAGENTS COMPLETE TESTING GUIDE

## ⚠️ CRITICAL SETUP - Do This First!

### 1️⃣ Add OpenRouter API Key to .env

You MUST have an OpenRouter API key. Get one from: https://openrouter.ai/keys

Then add it to your .env file:

```bash
# Open .env file
nano .env

# Add this line (replace with your actual key):
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxx

# Save and exit (Ctrl+X, then Y, then Enter)
```

---

## 📦 STEP 2: Install Dependencies

### Backend (Python):
```bash
cd /home/user/darkagents/backend
pip install -r requirements.txt
```

**Expected output:** "Successfully installed..." (takes 1-2 minutes)

### Frontend (Node.js):
```bash
cd /home/user/darkagents/frontend
npm install
```

**Expected output:** "added XXX packages" (takes 2-3 minutes)

---

## 🗄️ STEP 3: Set Up Database

### Check if PostgreSQL is running:
```bash
pg_isready
```

**Expected output:** "accepting connections" ✅

### Run database migrations:
```bash
cd /home/user/darkagents/backend
python -m alembic upgrade head
```

**Expected output:** "Running upgrade ... -> ..., <migration description>" ✅

**If migrations fail:**
```bash
# Reset database (WARNING: Deletes all data!)
python -m alembic downgrade base
python -m alembic upgrade head
```

---

## 🚀 STEP 4: Start Backend Server

### Open a NEW terminal window and run:
```bash
cd /home/user/darkagents/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ Backend is running at:** http://localhost:8000

### Test backend is working:
Open another terminal and run:
```bash
curl http://localhost:8000/health
```

**Expected output:** `{"status":"ok"}` ✅

---

## 🎨 STEP 5: Start Frontend Server

### Open a NEW terminal window (keep backend running) and run:
```bash
cd /home/user/darkagents/frontend
npm run dev
```

**Expected output:**
```
  ▲ Next.js 14.2.23
  - Local:        http://localhost:3000
  - Network:      http://0.0.0.0:3000

 ✓ Ready in 3.2s
```

**✅ Frontend is running at:** http://localhost:3000

---

## 🧪 STEP 6: Test the System

### Test 1: Access the Frontend
1. Open browser: http://localhost:3000
2. **Expected:** You see the DARKAGENTS homepage ✅

### Test 2: Create a New Project
1. Click "Create New Project" button
2. Enter project name: "Test SaaS App"
3. Enter idea: "A simple task management app for small teams"
4. Click "Create Project"
5. **Expected:** You're redirected to project dashboard ✅

### Test 3: Run Agent 01 (Product Manager)
1. On project dashboard, find "Agent 01: Product Manager"
2. Click "Run Agent" or "Start"
3. **Expected:** 
   - Status changes to "Working" ✅
   - Progress bar appears ✅
   - You see real-time updates via WebSocket ✅
4. **Wait 30-60 seconds** for agent to complete
5. **Expected:** Status changes to "Completed" ✅
6. Click "View Output" to see the PRD ✅

### Test 4: Check WebSocket Connection
**Open browser console (F12) and check:**
```
WebSocket connected to ws://localhost:8000/ws
```

**Expected:** You see ping/pong messages every 30 seconds ✅

### Test 5: Run All 10 Agents Sequential
1. Click "Run All Agents" button
2. **Expected:** Agents run one by one:
   - Agent 01: Product Manager ✅
   - Agent 02: System Architect ✅
   - Agent 03: Polyglot Developer ✅
   - Agent 04: UI/UX Designer ✅
   - Agent 05: QA Engineer ✅
   - Agent 06: Security Specialist ✅
   - Agent 07: DevOps Engineer ✅
   - Agent 08: Growth Marketer ✅
   - Agent 09: Business Strategist ✅
   - Agent 10: Platform Orchestrator ✅
3. **Total time:** 5-10 minutes for all agents
4. **Expected:** All agents complete successfully ✅

---

## 🐛 TROUBLESHOOTING

### Problem: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:**
```bash
cd /home/user/darkagents/backend
pip install -r requirements.txt
```

### Problem: "Error: Cannot find module 'next'"
**Solution:**
```bash
cd /home/user/darkagents/frontend
npm install
```

### Problem: "OPENROUTER_API_KEY not found"
**Solution:** Add the key to .env file (see Step 1)

### Problem: "Database connection failed"
**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready

# If not running, start it:
sudo service postgresql start
```

### Problem: "WebSocket connection failed"
**Solution:** 
1. Make sure backend is running on port 8000
2. Check browser console for errors
3. Try refreshing the page

### Problem: "Agent execution failed"
**Solutions:**
1. Check backend logs for errors
2. Verify OPENROUTER_API_KEY is correct
3. Check database has the AgentExecution table
4. Look for error messages in agent output

---

## 📊 EXPECTED RESULTS

### When Everything Works:

**Backend logs should show:**
```
INFO:     172.17.0.1:xxxxx - "POST /api/projects HTTP/1.1" 201
INFO:     172.17.0.1:xxxxx - "POST /api/agents/execute HTTP/1.1" 200
INFO:     WebSocket connection established
```

**Frontend should show:**
```
✅ Project created
✅ Agent 01 started
✅ Agent 01 completed (tokens: 5,234, cost: $0.08)
✅ PRD generated (2,450 words)
```

**Database should have:**
- 1 project record ✅
- 10 agent_execution records ✅
- Generated artifacts (PRD, architecture, code, etc.) ✅

---

## 🎯 SUCCESS CRITERIA

✅ Backend starts without errors
✅ Frontend starts without errors  
✅ Can create a project
✅ Agent 01 runs successfully
✅ Agent produces output (PRD)
✅ WebSocket shows real-time updates
✅ All 10 agents can run sequentially
✅ No errors in console or logs

---

## 📝 TESTING CHECKLIST

Copy this and check off as you test:

- [ ] OPENROUTER_API_KEY added to .env
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Database migrations run
- [ ] Backend server started (port 8000)
- [ ] Frontend server started (port 3000)
- [ ] Can access frontend in browser
- [ ] Can create a new project
- [ ] Agent 01 runs successfully
- [ ] Agent 01 produces output
- [ ] WebSocket connection works
- [ ] Can run all 10 agents
- [ ] All agents complete successfully
- [ ] No errors in backend logs
- [ ] No errors in browser console

---

## 🆘 IF SOMETHING BREAKS

**Send me:**
1. The exact error message
2. Backend logs (copy from terminal)
3. Browser console errors (F12 → Console)
4. Which step failed

**I'll help you fix it immediately!**

