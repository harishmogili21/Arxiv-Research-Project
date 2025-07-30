#!/usr/bin/env python3
"""
Clean arXiv MCP Server - Fixed version
"""

import json
import sys
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Global storage for paper context
paper_context: Dict[str, Dict] = {}

def search_arxiv_papers(query: str, max_results: int = 10, sort_by: str = "relevance") -> List[Dict[str, Any]]:
    """Search arXiv for research papers"""
    try:
        import arxiv
        
        sort_map = {
            "relevance": arxiv.SortCriterion.Relevance,
            "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
            "submittedDate": arxiv.SortCriterion.SubmittedDate
        }
        
        sort_criterion = sort_map.get(sort_by, arxiv.SortCriterion.Relevance)
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_criterion
        )
        
        results = []
        for paper in search.results():
            paper_data = {
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "abstract": paper.summary,
                "published": paper.published.isoformat(),
                "arxiv_id": paper.entry_id.split('/')[-1],
                "categories": paper.categories,
                "pdf_url": paper.pdf_url,
                "primary_category": paper.primary_category
            }
            results.append(paper_data)
            paper_context[paper_data["arxiv_id"]] = paper_data
        
        logger.info(f"Found {len(results)} papers for query: {query}")
        return results
        
    except ImportError:
        return [{"error": "arxiv module not available. Please install with: pip install arxiv"}]
    except Exception as e:
        logger.error(f"Error searching arXiv: {e}")
        return [{"error": f"Search failed: {str(e)}"}]

def get_paper_details(arxiv_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific paper"""
    try:
        import arxiv
        
        if arxiv_id in paper_context:
            return paper_context[arxiv_id]
        
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())
        
        paper_data = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "abstract": paper.summary,
            "published": paper.published.isoformat(),
            "updated": paper.updated.isoformat(),
            "arxiv_id": arxiv_id,
            "categories": paper.categories,
            "primary_category": paper.primary_category,
            "pdf_url": paper.pdf_url,
            "comment": getattr(paper, 'comment', ''),
            "journal_ref": getattr(paper, 'journal_ref', ''),
            "doi": getattr(paper, 'doi', '')
        }
        
        paper_context[arxiv_id] = paper_data
        return paper_data
        
    except ImportError:
        return {"error": "arxiv module not available. Please install with: pip install arxiv"}
    except Exception as e:
        logger.error(f"Error fetching paper {arxiv_id}: {e}")
        return {"error": f"Failed to fetch paper: {str(e)}"}

def analyze_paper_with_mistral(arxiv_id: str, question: str = "Provide a comprehensive analysis of this paper") -> Dict[str, Any]:
    """Analyze a paper using Mistral API"""
    try:
        from mistralai import Mistral
        
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            return {"error": "MISTRAL_API_KEY not configured"}
        
        mistral_client = Mistral(api_key=mistral_api_key)
        
        paper = get_paper_details(arxiv_id)
        if "error" in paper:
            return paper
        
        # Truncate abstract if too long
        abstract = paper['abstract']
        if len(abstract) > 2000:
            abstract = abstract[:2000] + "... [truncated]"
        
        paper_context_text = f"""
Title: {paper['title']}
Authors: {', '.join(paper['authors'])}
Published: {paper['published']}
Categories: {', '.join(paper['categories'])}
Abstract: {abstract}
"""
        
        analysis_prompt = f"""
Research Paper Analysis Request:

{paper_context_text}

Question/Analysis Request: {question}

Please provide a detailed analysis addressing the question while considering:
1. Key contributions and novelty
2. Methodology and approach
3. Results and implications
4. Strengths and limitations
5. Relevance to current research trends
"""
        
        # Use the standard chat completion API (no agent_id)
        response = mistral_client.chat.complete(
            model="mistral-small",
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        
        return {
            "arxiv_id": arxiv_id,
            "paper_title": paper['title'],
            "question": question,
            "analysis": response.choices[0].message.content,
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        return {"error": "mistralai module not available. Please install with: pip install mistralai"}
    except Exception as e:
        logger.error(f"Error analyzing paper with Mistral: {e}")
        return {"error": f"Analysis failed: {str(e)}"}

def chat_about_papers(message: str, paper_ids: List[str] = None) -> Dict[str, Any]:
    """Have a conversation about research papers using Mistral"""
    try:
        from mistralai import Mistral
        
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            return {"error": "MISTRAL_API_KEY not configured"}
        
        mistral_client = Mistral(api_key=mistral_api_key)
        
        papers_context = ""
        if paper_ids:
            for paper_id in paper_ids:
                paper = get_paper_details(paper_id)
                if "error" not in paper:
                    abstract = paper['abstract']
                    if len(abstract) > 500:
                        abstract = abstract[:500] + "... [truncated]"
                    
                    papers_context += f"""
Paper {paper_id}:
Title: {paper['title']}
Authors: {', '.join(paper['authors'])}
Abstract: {abstract}
---
"""
        
        system_prompt = "You are a research assistant helping analyze and discuss academic papers."
        if papers_context:
            system_prompt += f"\n\nCurrent papers in context:\n{papers_context}"
        
        # Use the standard chat completion API (no agent_id)
        response = mistral_client.chat.complete(
            model="mistral-small",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )
        
        return {
            "response": response.choices[0].message.content,
            "papers_in_context": paper_ids or [],
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        return {"error": "mistralai module not available. Please install with: pip install mistralai"}
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return {"error": f"Chat failed: {str(e)}"}

def compare_papers(paper_ids: List[str]) -> Dict[str, Any]:
    """Compare multiple research papers"""
    try:
        if len(paper_ids) < 2:
            return {"error": "Need at least 2 papers to compare"}
        
        papers = []
        for paper_id in paper_ids:
            paper = get_paper_details(paper_id)
            if "error" not in paper:
                papers.append(paper)
        
        if len(papers) < 2:
            return {"error": "Could not fetch enough papers for comparison"}
        
        comparison = {
            "papers": papers,
            "summary": {
                "total_papers": len(papers),
                "date_range": {
                    "earliest": min(p["published"] for p in papers),
                    "latest": max(p["published"] for p in papers)
                },
                "categories": list(set(cat for p in papers for cat in p["categories"])),
                "common_authors": list(set(author for p in papers for author in p["authors"]))
            }
        }
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing papers: {e}")
        return {"error": f"Comparison failed: {str(e)}"}

# MCP Protocol Implementation
def send_response(response):
    """Send JSON response to stdout"""
    print(json.dumps(response), flush=True)

def handle_initialize(request):
    """Handle MCP initialize request"""
    send_response({
        "jsonrpc": "2.0",
        "id": request["id"],
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "arxiv-research-server",
                "version": "1.0.0"
            }
        }
    })

def handle_tools_list(request):
    """Handle tools/list request"""
    tools = [
        {
            "name": "search_arxiv_papers",
            "description": "Search arXiv for research papers by keywords, authors, or topics",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "Search query (keywords, authors, titles)"
                    },
                    "max_results": {
                        "type": "integer", 
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "Sort order: relevance, lastUpdatedDate, submittedDate",
                        "default": "relevance"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_paper_details",
            "description": "Get detailed information about a specific arXiv paper",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "arxiv_id": {
                        "type": "string",
                        "description": "arXiv paper ID (e.g., '2301.07041')"
                    }
                },
                "required": ["arxiv_id"]
            }
        },
        {
            "name": "analyze_paper_with_mistral",
            "description": "Analyze a research paper using Mistral AI",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "arxiv_id": {
                        "type": "string",
                        "description": "arXiv paper ID to analyze"
                    },
                    "question": {
                        "type": "string",
                        "description": "Specific question or analysis request",
                        "default": "Provide a comprehensive analysis of this paper"
                    }
                },
                "required": ["arxiv_id"]
            }
        },
        {
            "name": "chat_about_papers",
            "description": "Have a conversation about research papers with AI assistance",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Your question or message about the papers"
                    },
                    "paper_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of arXiv paper IDs to include in context"
                    }
                },
                "required": ["message"]
            }
        },
        {
            "name": "compare_papers",
            "description": "Compare multiple research papers",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "paper_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of arXiv paper IDs to compare"
                    }
                },
                "required": ["paper_ids"]
            }
        }
    ]
    
    send_response({
        "jsonrpc": "2.0",
        "id": request["id"],
        "result": {"tools": tools}
    })

def handle_tools_call(request):
    """Handle tools/call request"""
    tool_name = request["params"]["name"]
    arguments = request["params"].get("arguments", {})
    
    try:
        if tool_name == "search_arxiv_papers":
            result = search_arxiv_papers(**arguments)
        elif tool_name == "get_paper_details":
            result = get_paper_details(**arguments)
        elif tool_name == "analyze_paper_with_mistral":
            result = analyze_paper_with_mistral(**arguments)
        elif tool_name == "chat_about_papers":
            result = chat_about_papers(**arguments)
        elif tool_name == "compare_papers":
            result = compare_papers(**arguments)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        send_response({
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        send_response({
            "jsonrpc": "2.0",
            "id": request["id"],
            "error": {
                "code": -32000,
                "message": f"Tool execution failed: {str(e)}"
            }
        })

def main():
    """Main MCP server loop"""
    logger.info("Starting clean arXiv MCP server")
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            try:
                request = json.loads(line)
                method = request.get("method")
                
                if method == "initialize":
                    handle_initialize(request)
                elif method == "tools/list":
                    handle_tools_list(request)
                elif method == "tools/call":
                    handle_tools_call(request)
                else:
                    logger.warning(f"Unknown method: {method}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                
    except KeyboardInterrupt:
        logger.info("Server shutting down")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()