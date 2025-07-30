#!/usr/bin/env python3
"""
Simple arXiv MCP Server
"""

import json
import sys
import os
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import arxiv
    from mistralai import Mistral
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Missing dependencies: {e}")
    DEPENDENCIES_AVAILABLE = False

# Initialize Mistral client if available
mistral_client = None
if DEPENDENCIES_AVAILABLE:
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if mistral_api_key:
        mistral_client = Mistral(api_key=mistral_api_key)

# Global storage
paper_context = {}

def search_arxiv_papers(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search arXiv for papers"""
    if not DEPENDENCIES_AVAILABLE:
        return [{"error": "Dependencies not available. Please install: pip install arxiv mistralai"}]
    
    try:
        search = arxiv.Search(query=query, max_results=max_results)
        results = []
        
        for paper in search.results():
            paper_data = {
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "abstract": paper.summary[:500] + "..." if len(paper.summary) > 500 else paper.summary,
                "published": paper.published.isoformat(),
                "arxiv_id": paper.entry_id.split('/')[-1],
                "categories": paper.categories,
                "pdf_url": paper.pdf_url
            }
            results.append(paper_data)
            paper_context[paper_data["arxiv_id"]] = paper_data
        
        return results
    except Exception as e:
        return [{"error": f"Search failed: {str(e)}"}]

def get_paper_details(arxiv_id: str) -> Dict[str, Any]:
    """Get paper details"""
    if not DEPENDENCIES_AVAILABLE:
        return {"error": "Dependencies not available"}
    
    try:
        if arxiv_id in paper_context:
            return paper_context[arxiv_id]
        
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())
        
        paper_data = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "abstract": paper.summary,
            "published": paper.published.isoformat(),
            "arxiv_id": arxiv_id,
            "categories": paper.categories,
            "pdf_url": paper.pdf_url
        }
        
        paper_context[arxiv_id] = paper_data
        return paper_data
    except Exception as e:
        return {"error": f"Failed to fetch paper: {str(e)}"}

def analyze_with_mistral(arxiv_id: str, question: str = "Analyze this paper") -> Dict[str, Any]:
    """Analyze paper with Mistral"""
    if not mistral_client:
        return {"error": "Mistral API not configured"}
    
    paper = get_paper_details(arxiv_id)
    if "error" in paper:
        return paper
    
    try:
        prompt = f"""
Paper: {paper['title']}
Authors: {', '.join(paper['authors'])}
Abstract: {paper['abstract'][:1000]}

Question: {question}

Please provide a detailed analysis of this research paper.
"""
        
        response = mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "arxiv_id": arxiv_id,
            "analysis": response.choices[0].message.content,
            "paper_title": paper['title']
        }
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

# MCP Protocol Handler
def main():
    """Main MCP protocol handler"""
    logger.info("Starting arXiv MCP Server")
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            
            if request.get("method") == "tools/list":
                tools = [
                    {
                        "name": "search_arxiv_papers",
                        "description": "Search arXiv for research papers",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query"},
                                "max_results": {"type": "integer", "default": 10}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_paper_details", 
                        "description": "Get detailed paper information",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "arxiv_id": {"type": "string", "description": "arXiv paper ID"}
                            },
                            "required": ["arxiv_id"]
                        }
                    },
                    {
                        "name": "analyze_with_mistral",
                        "description": "Analyze paper using Mistral AI",
                        "inputSchema": {
                            "type": "object", 
                            "properties": {
                                "arxiv_id": {"type": "string"},
                                "question": {"type": "string", "default": "Analyze this paper"}
                            },
                            "required": ["arxiv_id"]
                        }
                    }
                ]
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {"tools": tools}
                }
                print(json.dumps(response), flush=True)
                
            elif request.get("method") == "tools/call":
                tool_name = request["params"]["name"]
                arguments = request["params"].get("arguments", {})
                
                if tool_name == "search_arxiv_papers":
                    result = search_arxiv_papers(**arguments)
                elif tool_name == "get_paper_details":
                    result = get_paper_details(**arguments)
                elif tool_name == "analyze_with_mistral":
                    result = analyze_with_mistral(**arguments)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
                print(json.dumps(response), flush=True)
                
        except json.JSONDecodeError:
            continue
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -1, "message": str(e)}
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    main()