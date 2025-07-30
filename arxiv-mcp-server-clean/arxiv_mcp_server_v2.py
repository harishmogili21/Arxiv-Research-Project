#!/usr/bin/env python3
"""
arXiv MCP Server with Mistral Agents Integration - Simplified Version
"""

import json
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

import arxiv
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Mistral client
mistral_api_key = os.getenv("MISTRAL_API_KEY")
mistral_client = None
if mistral_api_key:
    mistral_client = Mistral(api_key=mistral_api_key)

# Global storage for paper context
paper_context: Dict[str, Dict] = {}

def count_tokens(text: str) -> int:
    """Rough token estimation"""
    return len(text.split()) * 1.3

def truncate_text(text: str, max_tokens: int = 4000) -> str:
    """Truncate text to fit within token limit"""
    if count_tokens(text) <= max_tokens:
        return text
    
    words = text.split()
    truncated = ""
    for word in words:
        test_text = truncated + " " + word if truncated else word
        if count_tokens(test_text) > max_tokens:
            break
        truncated = test_text
    
    return truncated + "... [truncated]"

def search_arxiv_papers(query: str, max_results: int = 10, sort_by: str = "relevance") -> List[Dict[str, Any]]:
    """Search arXiv for research papers"""
    try:
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
        
    except Exception as e:
        logger.error(f"Error searching arXiv: {e}")
        return [{"error": f"Search failed: {str(e)}"}]

def get_paper_details(arxiv_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific paper"""
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
        
    except Exception as e:
        logger.error(f"Error fetching paper {arxiv_id}: {e}")
        return {"error": f"Failed to fetch paper: {str(e)}"}

def analyze_paper_with_mistral(
    arxiv_id: str,
    question: str = "Provide a comprehensive analysis of this paper",
    agent_id: str = "ag:01234567-89ab-cdef-0123-456789abcdef"
) -> Dict[str, Any]:
    """Analyze a paper using Mistral's agents API"""
    try:
        if not mistral_client:
            return {"error": "Mistral API key not configured"}
        
        paper = get_paper_details(arxiv_id)
        if "error" in paper:
            return paper
        
        paper_context_text = f"""
Title: {paper['title']}
Authors: {', '.join(paper['authors'])}
Published: {paper['published']}
Categories: {', '.join(paper['categories'])}
Abstract: {paper['abstract']}
"""
        
        paper_context_text = truncate_text(paper_context_text, max_tokens=3000)
        
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
        
        try:
            response = mistral_client.agents.complete(
                agent_id=agent_id,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
        except Exception:
            response = mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": analysis_prompt}]
            )
        
        return {
            "arxiv_id": arxiv_id,
            "paper_title": paper['title'],
            "question": question,
            "analysis": response.choices[0].message.content,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing paper with Mistral: {e}")
        return {"error": f"Analysis failed: {str(e)}"}

def chat_about_papers(
    message: str,
    paper_ids: List[str] = None,
    conversation_history: List[Dict[str, str]] = None,
    agent_id: str = "ag:01234567-89ab-cdef-0123-456789abcdef"
) -> Dict[str, Any]:
    """Have a conversation about research papers"""
    try:
        if not mistral_client:
            return {"error": "Mistral API key not configured"}
        
        papers_context = ""
        if paper_ids:
            for paper_id in paper_ids:
                paper = get_paper_details(paper_id)
                if "error" not in paper:
                    papers_context += f"""
Paper {paper_id}:
Title: {paper['title']}
Authors: {', '.join(paper['authors'])}
Abstract: {truncate_text(paper['abstract'], 500)}
---
"""
        
        messages = []
        
        if papers_context:
            system_message = f"""You are a research assistant helping analyze and discuss academic papers. 

Current papers in context:
{papers_context}

Please provide helpful, accurate responses about these papers and related research topics."""
            messages.append({"role": "system", "content": system_message})
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": message})
        
        try:
            response = mistral_client.agents.complete(
                agent_id=agent_id,
                messages=messages
            )
        except Exception:
            response = mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=messages
            )
        
        return {
            "response": response.choices[0].message.content,
            "papers_in_context": paper_ids or [],
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return {"error": f"Chat failed: {str(e)}"}

def compare_papers(paper_ids: List[str], comparison_aspects: List[str] = None) -> Dict[str, Any]:
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
        
        if not comparison_aspects:
            comparison_aspects = [
                "methodology",
                "key_contributions", 
                "datasets_used",
                "performance_metrics",
                "publication_timeline"
            ]
        
        comparison = {
            "papers": papers,
            "comparison_aspects": comparison_aspects,
            "summary": {
                "total_papers": len(papers),
                "date_range": {
                    "earliest": min(p["published"] for p in papers),
                    "latest": max(p["published"] for p in papers)
                },
                "categories": list(set(cat for p in papers for cat in p["categories"])),
                "authors": list(set(author for p in papers for author in p["authors"]))
            }
        }
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing papers: {e}")
        return {"error": f"Comparison failed: {str(e)}"}

# MCP Protocol Implementation
def handle_mcp_request():
    """Handle MCP protocol requests"""
    try:
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
                                    "max_results": {"type": "integer", "default": 10},
                                    "sort_by": {"type": "string", "default": "relevance"}
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "get_paper_details",
                            "description": "Get detailed information about a specific paper",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "arxiv_id": {"type": "string", "description": "arXiv paper ID"}
                                },
                                "required": ["arxiv_id"]
                            }
                        },
                        {
                            "name": "analyze_paper_with_mistral",
                            "description": "Analyze a paper using Mistral agents",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "arxiv_id": {"type": "string"},
                                    "question": {"type": "string", "default": "Provide a comprehensive analysis"},
                                    "agent_id": {"type": "string", "default": "ag:01234567-89ab-cdef-0123-456789abcdef"}
                                },
                                "required": ["arxiv_id"]
                            }
                        },
                        {
                            "name": "chat_about_papers",
                            "description": "Chat about research papers",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "paper_ids": {"type": "array", "items": {"type": "string"}},
                                    "conversation_history": {"type": "array"},
                                    "agent_id": {"type": "string", "default": "ag:01234567-89ab-cdef-0123-456789abcdef"}
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
                                    "paper_ids": {"type": "array", "items": {"type": "string"}},
                                    "comparison_aspects": {"type": "array", "items": {"type": "string"}}
                                },
                                "required": ["paper_ids"]
                            }
                        }
                    ]
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"tools": tools}
                    }
                    print(json.dumps(response))
                    
                elif request.get("method") == "tools/call":
                    tool_name = request["params"]["name"]
                    arguments = request["params"].get("arguments", {})
                    
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
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
                    }
                    print(json.dumps(response))
                    
            except json.JSONDecodeError:
                continue
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {"code": -1, "message": str(e)}
                }
                print(json.dumps(error_response))
                
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    if not mistral_api_key:
        logger.warning("MISTRAL_API_KEY not found in environment variables")
    
    handle_mcp_request()