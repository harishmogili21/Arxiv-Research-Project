#!/usr/bin/env python3
"""
arXiv MCP Server with Mistral Agents Integration
Provides tools for searching, retrieving, and analyzing research papers using agentic RAG
"""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

import arxiv
import httpx
from mistralai import Mistral
from pydantic import BaseModel
import tiktoken
from dotenv import load_dotenv

from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("arXiv Research Assistant")

# Initialize Mistral client
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaperSummary(BaseModel):
    """Model for paper summary data"""
    title: str
    authors: List[str]
    abstract: str
    published: str
    arxiv_id: str
    categories: List[str]
    pdf_url: str

class ChatMessage(BaseModel):
    """Model for chat messages"""
    role: str
    content: str

# Global storage for paper context
paper_context: Dict[str, Dict] = {}

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback to rough estimation
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

@mcp.tool()
def search_arxiv_papers(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance"
) -> List[Dict[str, Any]]:
    """
    Search arXiv for research papers
    
    Args:
        query: Search query (can include keywords, authors, titles)
        max_results: Maximum number of results to return (default: 10)
        sort_by: Sort order - 'relevance', 'lastUpdatedDate', 'submittedDate' (default: relevance)
    
    Returns:
        List of paper summaries with metadata
    """
    try:
        # Map sort options
        sort_map = {
            "relevance": arxiv.SortCriterion.Relevance,
            "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
            "submittedDate": arxiv.SortCriterion.SubmittedDate
        }
        
        sort_criterion = sort_map.get(sort_by, arxiv.SortCriterion.Relevance)
        
        # Search arXiv
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
            
            # Store in context for later use
            paper_context[paper_data["arxiv_id"]] = paper_data
        
        logger.info(f"Found {len(results)} papers for query: {query}")
        return results
        
    except Exception as e:
        logger.error(f"Error searching arXiv: {e}")
        return [{"error": f"Search failed: {str(e)}"}]

@mcp.tool()
def get_paper_details(arxiv_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific paper by arXiv ID
    
    Args:
        arxiv_id: arXiv paper ID (e.g., "2301.07041")
    
    Returns:
        Detailed paper information
    """
    try:
        # Check if we have it in context first
        if arxiv_id in paper_context:
            return paper_context[arxiv_id]
        
        # Otherwise fetch from arXiv
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
        
        # Store in context
        paper_context[arxiv_id] = paper_data
        
        return paper_data
        
    except Exception as e:
        logger.error(f"Error fetching paper {arxiv_id}: {e}")
        return {"error": f"Failed to fetch paper: {str(e)}"}

@mcp.tool()
def analyze_paper_with_mistral(
    arxiv_id: str,
    question: str = "Provide a comprehensive analysis of this paper",
    agent_id: str = "ag:01234567-89ab-cdef-0123-456789abcdef"
) -> Dict[str, Any]:
    """
    Analyze a paper using Mistral's agents API
    
    Args:
        arxiv_id: arXiv paper ID
        question: Specific question or analysis request
        agent_id: Mistral agent ID to use for analysis
    
    Returns:
        Analysis results from Mistral agent
    """
    try:
        # Get paper details
        paper = get_paper_details(arxiv_id)
        if "error" in paper:
            return paper
        
        # Prepare context for the agent
        paper_context_text = f"""
Title: {paper['title']}
Authors: {', '.join(paper['authors'])}
Published: {paper['published']}
Categories: {', '.join(paper['categories'])}
Abstract: {paper['abstract']}
"""
        
        # Truncate if too long
        paper_context_text = truncate_text(paper_context_text, max_tokens=3000)
        
        # Create the analysis prompt
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
        
        # Call Mistral agent
        try:
            response = mistral_client.agents.complete(
                agent_id=agent_id,
                messages=[
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ]
            )
        except Exception as e:
            # Fallback to regular chat completion if agents API fails
            response = mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ]
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

@mcp.tool()
def chat_about_papers(
    message: str,
    paper_ids: List[str] = None,
    conversation_history: List[Dict[str, str]] = None,
    agent_id: str = "ag:01234567-89ab-cdef-0123-456789abcdef"
) -> Dict[str, Any]:
    """
    Have a conversation about research papers using Mistral agents
    
    Args:
        message: User message/question
        paper_ids: List of arXiv IDs to include in context (optional)
        conversation_history: Previous conversation messages (optional)
        agent_id: Mistral agent ID to use
    
    Returns:
        Agent response with conversation context
    """
    try:
        # Build context from papers
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
        
        # Prepare messages
        messages = []
        
        # Add system context if we have papers
        if papers_context:
            system_message = f"""You are a research assistant helping analyze and discuss academic papers. 

Current papers in context:
{papers_context}

Please provide helpful, accurate responses about these papers and related research topics."""
            messages.append({"role": "system", "content": system_message})
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Call Mistral agent
        try:
            response = mistral_client.agents.complete(
                agent_id=agent_id,
                messages=messages
            )
        except Exception as e:
            # Fallback to regular chat completion if agents API fails
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

@mcp.tool()
def compare_papers(
    paper_ids: List[str],
    comparison_aspects: List[str] = None
) -> Dict[str, Any]:
    """
    Compare multiple research papers
    
    Args:
        paper_ids: List of arXiv IDs to compare
        comparison_aspects: Specific aspects to compare (optional)
    
    Returns:
        Comparison analysis
    """
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
        
        # Default comparison aspects
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

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("MISTRAL_API_KEY"):
        logger.warning("MISTRAL_API_KEY not found in environment variables")
    
    mcp.run()