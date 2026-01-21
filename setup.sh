#!/bin/bash

# Resolution Backend - Local Setup Script
# This script helps you set up your local development environment

set -e  # Exit on error

echo "🚀 Resolution Backend - Local Setup"
echo "===================================="
echo ""

# Check Python version
echo "1️⃣  Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
if (( $(echo "$python_version >= 3.11" | bc -l) )); then
    echo "✅ Python $python_version detected"
else
    echo "❌ Python 3.11+ required (found $python_version)"
    exit 1
fi

# Check uv
echo ""
echo "2️⃣  Checking uv package manager..."
if command -v uv &> /dev/null; then
    uv_version=$(uv --version | grep -oP '\d+\.\d+\.\d+')
    echo "✅ uv $uv_version detected"
else
    echo "❌ uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ uv installed"
fi

# Check .env file
echo ""
echo "3️⃣  Checking environment configuration..."
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    if grep -q "sk-" .env; then
        echo "✅ OpenAI API key detected"
    else
        echo "⚠️  .env exists but may need valid API key"
    fi
else
    echo "⚠️  .env file not found"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "❗ IMPORTANT: Edit .env and add your OpenAI API key!"
    echo "   Run: nano .env"
    echo "   Or open in Cursor and replace: sk-your-key-here"
    echo ""
fi

# Install dependencies
echo ""
echo "4️⃣  Installing dependencies..."
uv sync
echo "✅ Dependencies installed"

# Check test documents
echo ""
echo "5️⃣  Checking test documents..."
if [ -d "dataset/documents" ] && [ "$(ls -A dataset/documents)" ]; then
    doc_count=$(ls -1 dataset/documents/*.md 2>/dev/null | wc -l)
    echo "✅ Found $doc_count test documents"

    # Check for required documents
    if [ -f "dataset/documents/O - Statement of Claim.md" ] && [ -f "dataset/documents/P - Statement of Defence.md" ]; then
        echo "✅ Required documents present (Statement of Claim & Defence)"
    else
        echo "⚠️  Required documents missing (O - Statement of Claim.md, P - Statement of Defence.md)"
    fi
else
    echo "⚠️  No documents found in dataset/documents/"
fi

# Test imports
echo ""
echo "6️⃣  Testing imports..."
if uv run python -c "from src.utils.prompts import PROMPT_REGISTRY; from src.orchestrator.deep_agent import CourtIssueDeepAgent" 2>/dev/null; then
    echo "✅ All imports successful"
else
    echo "❌ Import errors detected"
    exit 1
fi

# Summary
echo ""
echo "===================================="
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your OpenAI API key (if not done)"
echo "  2. Start dev server: uv run langgraph dev"
echo "  3. In another terminal, test: curl http://localhost:2024/agent/status"
echo "  4. Run full test: curl -X POST http://localhost:2024/agent/start"
echo ""
echo "For detailed instructions, see: LOCAL_SETUP.md"
echo "===================================="
