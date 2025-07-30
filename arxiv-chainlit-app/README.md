# 🔬 arXiv Paper Chat - Chainlit UI

A conversational interface for searching, analyzing, and chatting with arXiv research papers using AI.

## 🚀 Features

- **Smart Paper Search**: Find relevant research papers on arXiv
- **AI-Powered Analysis**: Get detailed paper analysis using Mistral AI
- **Interactive Conversations**: Chat naturally about research papers
- **Multi-Paper Context**: Compare and discuss multiple papers simultaneously
- **Command-Based Interface**: Easy-to-use commands for different actions

## 📦 Installation

1. **Clone and navigate to the directory:**
```bash
cd arxiv-chainlit-app
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
chainlit run app.py -w
```

4. **Open your browser** to `http://localhost:8000`

## 🎯 Usage

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/search <query>` | Search for papers | `/search neural machine translation` |
| `/select <number>` | Select paper from results | `/select 1` |
| `/papers` | Show selected papers | `/papers` |
| `/analyze <arxiv_id>` | Analyze specific paper | `/analyze 2203.14263v1` |

### Workflow

1. **Search for papers:**
   ```
   /search attention mechanisms
   ```

2. **Select interesting papers:**
   ```
   /select 1
   /select 3
   ```

3. **Start chatting:**
   ```
   What are the main differences between these attention mechanisms?
   Which approach would be better for real-time applications?
   ```

## 🔧 MCP Integration

The app currently uses mock responses. To integrate with your actual MCP server:

1. **Update `mcp_integration.py`** with your MCP client configuration
2. **Replace the mock client** in `app.py` with `RealArxivMCPClient`
3. **Configure your MCP server** connection details

Example integration:
```python
# In app.py, replace:
mcp_client = ArxivMCPClient()

# With:
from mcp_integration import RealArxivMCPClient
mcp_client = RealArxivMCPClient()
```

## 🎨 Customization

### UI Themes
Edit `.chainlit/config.toml` to customize:
- Colors and themes
- App name and description
- UI layout and behavior

### Features
Modify `app.py` to add:
- Additional commands
- Custom paper filtering
- Enhanced AI prompts
- Export functionality

## 📁 Project Structure

```
arxiv-chainlit-app/
├── app.py                 # Main Chainlit application
├── mcp_integration.py     # MCP client integration
├── requirements.txt       # Python dependencies
├── chainlit.md           # Welcome page content
├── .chainlit/
│   └── config.toml       # Chainlit configuration
└── README.md             # This file
```

## 🤖 AI Capabilities

The app leverages Mistral AI through MCP to:
- Analyze paper methodology and contributions
- Compare multiple research approaches
- Answer questions about technical details
- Provide insights on practical applications
- Suggest related work and future directions

## 🔍 Example Interactions

**Search and Select:**
```
User: /search transformer architecture
Bot: 📚 Found 5 papers for 'transformer architecture'...

User: /select 1
Bot: ✅ Added to chat context: "Attention Is All You Need"

User: What makes the transformer architecture unique?
Bot: 🤖 The transformer architecture is unique because...
```

**Multi-Paper Analysis:**
```
User: /select 2
User: /select 3
User: Compare the attention mechanisms in these three papers
Bot: 🤖 Comparing the attention mechanisms across these papers...
```

## 🛠️ Development

To extend the application:

1. **Add new commands** in the `main()` function
2. **Enhance AI prompts** in the MCP integration
3. **Customize UI** through the Chainlit config
4. **Add paper filtering** and advanced search options

## 📝 License

This project is open source. Feel free to modify and distribute.

---

*Built with ❤️ using Chainlit, arXiv API, and Mistral AI*