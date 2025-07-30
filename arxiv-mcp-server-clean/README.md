# arXiv MCP Server with Mistral Agents

An MCP (Model Context Protocol) server that provides intelligent research paper analysis using arXiv and Mistral's agents API for agentic RAG (Retrieval-Augmented Generation).

## Features

- **Paper Search**: Search arXiv for research papers by keywords, authors, or topics
- **Paper Retrieval**: Get detailed information about specific papers
- **Agentic Analysis**: Use Mistral agents to analyze papers with custom questions
- **Interactive Chat**: Have conversations about papers with context awareness
- **Paper Comparison**: Compare multiple papers across different aspects
- **Token Management**: Automatic text truncation to stay within API limits

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Mistral API key and agent ID
```

3. Configure in Kiro's MCP settings (`.kiro/settings/mcp.json`):
```json
{
  "mcpServers": {
    "arxiv-research": {
      "command": "python",
      "args": ["arxiv_mcp_server.py"],
      "env": {
        "MISTRAL_API_KEY": "${MISTRAL_API_KEY}"
      },
      "disabled": false,
      "autoApprove": ["search_arxiv_papers", "get_paper_details"]
    }
  }
}
```

## Available Tools

### `search_arxiv_papers`
Search for research papers on arXiv
- `query`: Search terms (keywords, authors, titles)
- `max_results`: Number of results (default: 10)
- `sort_by`: Sort order - 'relevance', 'lastUpdatedDate', 'submittedDate'

### `get_paper_details`
Get detailed information about a specific paper
- `arxiv_id`: arXiv paper ID (e.g., "2301.07041")

### `analyze_paper_with_mistral`
Analyze a paper using Mistral agents
- `arxiv_id`: Paper to analyze
- `question`: Specific analysis question
- `agent_id`: Mistral agent ID to use

### `chat_about_papers`
Interactive conversation about papers
- `message`: Your question or comment
- `paper_ids`: Papers to include in context
- `conversation_history`: Previous messages
- `agent_id`: Mistral agent ID

### `compare_papers`
Compare multiple research papers
- `paper_ids`: List of papers to compare
- `comparison_aspects`: Specific aspects to focus on

## Usage Examples

1. **Search for papers**:
   ```
   Search for papers about "transformer attention mechanisms"
   ```

2. **Analyze a specific paper**:
   ```
   Analyze paper 2301.07041 and explain its key contributions
   ```

3. **Chat about papers**:
   ```
   I have papers 2301.07041 and 2302.12345 in context. How do their approaches to attention differ?
   ```

4. **Compare papers**:
   ```
   Compare papers 2301.07041, 2302.12345, and 2303.56789 focusing on methodology and performance
   ```

## Architecture

The server combines:
- **arXiv API**: For paper search and metadata retrieval
- **Mistral Agents API**: For intelligent analysis and conversation
- **FastMCP**: For MCP protocol implementation
- **Context Management**: Maintains paper context across interactions

## Requirements

- Python 3.8+
- Mistral API key
- Internet connection for arXiv and Mistral API access