# 🔬 arXiv Research Project

A comprehensive research assistant system that combines arXiv paper search, AI-powered analysis, and conversational interfaces using MCP (Model Context Protocol) and Mistral AI.

## 🌟 Features

- **Intelligent Paper Search**: Find relevant research papers on arXiv by keywords, authors, or topics
- **AI-Powered Analysis**: Get detailed paper analysis using Mistral AI
- **Interactive Chat Interface**: Have natural conversations about research papers
- **Multi-Paper Comparison**: Compare and analyze multiple papers simultaneously
- **MCP Integration**: Seamless integration with Kiro IDE through Model Context Protocol
- **Web UI**: User-friendly Chainlit-based web interface

## 🏗️ Project Structure

```
arxiv-research-project/
├── arxiv-mcp-server-clean/     # MCP Server for arXiv + Mistral integration
│   ├── arxiv_mcp_clean.py      # Main MCP server implementation
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example           # Environment variables template
│   └── README.md              # Server-specific documentation
├── arxiv-chainlit-app/        # Web UI using Chainlit
│   ├── app.py                 # Main Chainlit application
│   ├── mcp_integration.py     # MCP client integration
│   ├── requirements.txt       # UI dependencies
│   └── README.md              # UI-specific documentation
├── .kiro/                     # Kiro IDE configuration
│   └── settings/
│       └── mcp.json          # MCP server configuration
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/harishmogili21/Arxiv-Research-Project.git
cd Arxiv-Research-Project
```

### 2. Set Up Environment Variables

```bash
# Copy environment template
cp arxiv-mcp-server-clean/.env.example arxiv-mcp-server-clean/.env
cp arxiv-chainlit-app/.env.example arxiv-chainlit-app/.env

# Edit .env files with your Mistral API key
# Get your API key from: https://console.mistral.ai/
```

### 3. Install Dependencies

```bash
# For MCP Server
cd arxiv-mcp-server-clean
pip install -r requirements.txt

# For Web UI
cd ../arxiv-chainlit-app
pip install -r requirements.txt
```

### 4. Run the Applications

**Option A: MCP Server (for Kiro IDE integration)**
```bash
cd arxiv-mcp-server-clean
python arxiv_mcp_clean.py
```

**Option B: Web UI (for browser-based interface)**
```bash
cd arxiv-chainlit-app
chainlit run app.py -w
```

## 🔧 Configuration

### MCP Server Configuration

Update `.kiro/settings/mcp.json` for Kiro IDE integration:

```json
{
  "mcpServers": {
    "arxiv-research": {
      "command": "python",
      "args": ["-u", "arxiv-mcp-server-clean/arxiv_mcp_clean.py"],
      "env": {
        "MISTRAL_API_KEY": "${MISTRAL_API_KEY}",
        "PYTHONUNBUFFERED": "1"
      },
      "disabled": false,
      "autoApprove": [
        "search_arxiv_papers",
        "get_paper_details",
        "analyze_paper_with_mistral",
        "chat_about_papers",
        "compare_papers"
      ]
    }
  }
}
```

### Environment Variables

Required environment variables in your `.env` files:

```bash
# Mistral AI API Key (required)
MISTRAL_API_KEY=your_mistral_api_key_here

# Optional: Logging level
LOG_LEVEL=INFO
```

## 🎯 Usage Examples

### MCP Server Functions

1. **Search for papers**:
   ```python
   search_arxiv_papers("transformer attention mechanisms", max_results=5)
   ```

2. **Get paper details**:
   ```python
   get_paper_details("2410.15578v1")
   ```

3. **Analyze with AI**:
   ```python
   analyze_paper_with_mistral("2410.15578v1", "What are the key innovations?")
   ```

4. **Chat about papers**:
   ```python
   chat_about_papers("Compare these attention mechanisms", ["2410.15578v1", "2303.01542v1"])
   ```

5. **Compare papers**:
   ```python
   compare_papers(["2410.15578v1", "2303.01542v1"])
   ```

### Web UI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/search <query>` | Search for papers | `/search neural machine translation` |
| `/select <number>` | Select paper from results | `/select 1` |
| `/papers` | Show selected papers | `/papers` |
| `/analyze <arxiv_id>` | Analyze specific paper | `/analyze 2203.14263v1` |

## 🛠️ Development

### Adding New Features

1. **MCP Server**: Extend `arxiv_mcp_clean.py` with new functions
2. **Web UI**: Add new commands in `arxiv-chainlit-app/app.py`
3. **Integration**: Update MCP configuration to include new tools

### Testing

```bash
# Test MCP server functions
cd arxiv-mcp-server-clean
python -c "from arxiv_mcp_clean import search_arxiv_papers; print(search_arxiv_papers('test'))"

# Test web UI
cd arxiv-chainlit-app
chainlit run app.py
```

## 📋 Requirements

- Python 3.8+
- Mistral AI API key
- Internet connection for arXiv and Mistral API access
- Kiro IDE (for MCP integration) or web browser (for Chainlit UI)

## 🔒 Security

- All API keys are stored in `.env` files (not tracked by git)
- Sensitive data is masked in configuration files
- Environment variables are used for all secrets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source. Feel free to modify and distribute.

## 🙏 Acknowledgments

- [arXiv](https://arxiv.org/) for providing access to research papers
- [Mistral AI](https://mistral.ai/) for powerful language models
- [Chainlit](https://chainlit.io/) for the conversational UI framework
- [MCP](https://modelcontextprotocol.io/) for the integration protocol

---

*Built with ❤️ for researchers and AI enthusiasts*