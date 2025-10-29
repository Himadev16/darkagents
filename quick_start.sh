#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     🚀 DARKAGENTS QUICK START - Testing Commands             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check current directory
cd /home/user/darkagents

# Step 1: Check OpenRouter API Key
echo "Step 1: Checking OPENROUTER_API_KEY..."
if grep -q "OPENROUTER_API_KEY" .env; then
    echo "✅ OPENROUTER_API_KEY found"
else
    echo "❌ OPENROUTER_API_KEY NOT FOUND!"
    echo ""
    echo "YOU MUST ADD IT TO .env FILE:"
    echo "1. Get key from: https://openrouter.ai/keys"
    echo "2. Run: nano .env"
    echo "3. Add line: OPENROUTER_API_KEY=sk-or-v1-xxxxx"
    echo "4. Save (Ctrl+X, Y, Enter)"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Step 2: Check database
echo ""
echo "Step 2: Checking PostgreSQL..."
if pg_isready > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is NOT running"
    echo "Start it with: sudo service postgresql start"
    exit 1
fi

# Step 3: Check Python dependencies
echo ""
echo "Step 3: Checking Python dependencies..."
cd backend
if python -c "import fastapi" 2>/dev/null; then
    echo "✅ Backend dependencies installed"
else
    echo "⚠️  Installing backend dependencies (takes 1-2 minutes)..."
    pip install -r requirements.txt
fi

# Step 4: Check Node dependencies
echo ""
echo "Step 4: Checking Node.js dependencies..."
cd ../frontend
if [ -d "node_modules" ]; then
    echo "✅ Frontend dependencies installed"
else
    echo "⚠️  Installing frontend dependencies (takes 2-3 minutes)..."
    npm install
fi

# Step 5: Run migrations
echo ""
echo "Step 5: Running database migrations..."
cd ../backend
python -m alembic upgrade head

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  ✅ SETUP COMPLETE!                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 NEXT STEPS:"
echo ""
echo "1️⃣  START BACKEND (in this terminal):"
echo "    cd /home/user/darkagents/backend"
echo "    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2️⃣  START FRONTEND (in a NEW terminal):"
echo "    cd /home/user/darkagents/frontend"
echo "    npm run dev"
echo ""
echo "3️⃣  OPEN BROWSER:"
echo "    http://localhost:3000"
echo ""
echo "4️⃣  CREATE PROJECT & TEST AGENTS!"
echo ""

