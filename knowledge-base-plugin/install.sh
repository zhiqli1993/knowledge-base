#!/bin/bash

set -e

echo "🚀 Knowledge Base Plugin Installer"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama not found${NC}"
    echo "   Install from: https://ollama.com/download"
    echo "   Or run: curl -fsSL https://ollama.com/install.sh | sh"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} Ollama found"

    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✓${NC} Ollama is running"

        # Check if nomic-embed-text model is installed
        if ollama list | grep -q "nomic-embed-text"; then
            echo -e "${GREEN}✓${NC} nomic-embed-text model installed"
        else
            echo -e "${YELLOW}⚠️  nomic-embed-text model not found${NC}"
            read -p "Pull the model now? (Y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                echo "Pulling nomic-embed-text model..."
                ollama pull nomic-embed-text
                echo -e "${GREEN}✓${NC} Model pulled successfully"
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  Ollama is not running${NC}"
        echo "   Start with: ollama serve"
    fi
fi

# Check Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is required but not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Git found"

echo ""
echo "Installing Python dependencies..."

# Install requirements
if [ -f "requirements.txt" ]; then
    pip3 install -q -r requirements.txt
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found, skipping dependency installation${NC}"
fi

echo ""
echo "Setting up directories..."

# Create config directory
CONFIG_DIR="$HOME/.kb"
mkdir -p "$CONFIG_DIR"
echo -e "${GREEN}✓${NC} Config directory: $CONFIG_DIR"

# Create default config if not exists
CONFIG_FILE="$CONFIG_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" <<EOF
{
  "chroma": {
    "persist_directory": "~/.local/share/knowledge-base/chroma",
    "collection_name": "knowledge_base"
  },
  "ollama": {
    "host": "localhost",
    "port": 11434,
    "model": "nomic-embed-text",
    "timeout": 60
  },
  "indexing": {
    "chunk_size": 1000,
    "chunk_overlap": 200
  },
  "github": {
    "max_file_size_mb": 5,
    "auto_detect_language": true
  },
  "web": {
    "timeout": 30,
    "max_pages_per_site": 100,
    "user_agent": "KnowledgeBase/1.0"
  }
}
EOF
    echo -e "${GREEN}✓${NC} Created default config: $CONFIG_FILE"
else
    echo -e "${GREEN}✓${NC} Config already exists: $CONFIG_FILE"
fi

# Create storage directory
STORAGE_DIR="$HOME/.local/share/knowledge-base"
mkdir -p "$STORAGE_DIR"
echo -e "${GREEN}✓${NC} Storage directory: $STORAGE_DIR"

# Install skill
SKILLS_DIR="$HOME/.claude/skills"
mkdir -p "$SKILLS_DIR"

if [ -d "$SKILLS_DIR/knowledge-base" ]; then
    echo -e "${YELLOW}⚠️  Skill already exists, backing up...${NC}"
    mv "$SKILLS_DIR/knowledge-base" "$SKILLS_DIR/knowledge-base.backup.$(date +%s)"
fi

cp -r skills/knowledge-base "$SKILLS_DIR/"
echo -e "${GREEN}✓${NC} Skill installed: $SKILLS_DIR/knowledge-base"

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "📚 Next steps:"
echo "  1. Ensure Ollama is running: ollama serve"
echo "  2. Restart Claude Code to load the new skill"
echo "  3. Try it: \"Add anthropics/anthropic-quickstarts to my knowledge base\""
echo ""
echo "📖 Documentation:"
echo "  - README.md - Plugin overview"
echo "  - QUICKSTART.md - Minimal setup guide"
echo "  - LANGUAGE_DETECTION.md - Repo indexing exclude behavior"
echo ""
echo "🔧 Testing:"
echo "  - Run tests: python3 tests/e2e/test_kb_e2e.py"
echo "  - CLI tool: kb status"
echo ""
