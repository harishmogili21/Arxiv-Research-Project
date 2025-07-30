import chainlit as cl
import asyncio
import json
from typing import List, Dict, Any
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ArxivMCPClient:
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        # Store paper context for analysis
        self.paper_context = {}
    
    async def search_papers(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search arXiv papers using direct API"""
        try:
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            papers = []
            
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                paper = {
                    'title': entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
                    'authors': [author.find('{http://www.w3.org/2005/Atom}name').text 
                               for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
                    'abstract': entry.find('{http://www.w3.org/2005/Atom}summary').text.strip(),
                    'published': entry.find('{http://www.w3.org/2005/Atom}published').text,
                    'arxiv_id': entry.find('{http://www.w3.org/2005/Atom}id').text.split('/')[-1],
                    'pdf_url': entry.find('{http://www.w3.org/2005/Atom}id').text.replace('abs', 'pdf'),
                    'categories': [cat.get('term') for cat in entry.findall('{http://arxiv.org/schemas/atom}primary_category')]
                }
                papers.append(paper)
                # Store for later analysis
                self.paper_context[paper['arxiv_id']] = paper
            
            return papers
        except Exception as e:
            print(f"Error searching papers: {e}")
            return []
    
    async def analyze_paper(self, arxiv_id: str, question: str = "Provide a comprehensive analysis") -> Dict:
        """Analyze paper using Mistral API"""
        try:
            from mistralai import Mistral
            
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            if not mistral_api_key:
                return {
                    'arxiv_id': arxiv_id,
                    'question': question,
                    'analysis': "Error: MISTRAL_API_KEY not configured. Please set your Mistral API key as an environment variable.",
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get paper details
            paper = self.paper_context.get(arxiv_id)
            if not paper:
                # Try to fetch paper details
                paper = await self._fetch_paper_details(arxiv_id)
            
            if not paper:
                return {
                    'arxiv_id': arxiv_id,
                    'question': question,
                    'analysis': f"Error: Could not fetch details for paper {arxiv_id}",
                    'timestamp': datetime.now().isoformat()
                }
            
            mistral_client = Mistral(api_key=mistral_api_key)
            
            # Truncate abstract if too long
            abstract = paper['abstract']
            if len(abstract) > 2000:
                abstract = abstract[:2000] + "... [truncated]"
            
            paper_context_text = f"""
Title: {paper['title']}
Authors: {', '.join(paper['authors'])}
Published: {paper['published']}
Categories: {', '.join(paper.get('categories', []))}
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
            
            # Use Mistral chat API
            response = mistral_client.chat.complete(
                model="mistral-small",
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            analysis_content = response.choices[0].message.content
            
            return {
                'arxiv_id': arxiv_id,
                'question': question,
                'analysis': analysis_content,
                'timestamp': datetime.now().isoformat()
            }
            
        except ImportError:
            return {
                'arxiv_id': arxiv_id,
                'question': question,
                'analysis': "Error: mistralai module not available. Please install with: pip install mistralai",
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'arxiv_id': arxiv_id,
                'question': question,
                'analysis': f"Error analyzing paper: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    async def chat_about_papers(self, message: str, paper_ids: List[str]) -> Dict:
        """Chat about papers using Mistral API"""
        try:
            from mistralai import Mistral
            
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            if not mistral_api_key:
                return {
                    'response': "Error: MISTRAL_API_KEY not configured. Please set your Mistral API key as an environment variable.",
                    'papers_in_context': paper_ids,
                    'timestamp': datetime.now().isoformat()
                }
            
            mistral_client = Mistral(api_key=mistral_api_key)
            
            # Build context from selected papers
            papers_context = ""
            for paper_id in paper_ids:
                paper = self.paper_context.get(paper_id)
                if paper:
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
            
            # Use Mistral chat API
            response = mistral_client.chat.complete(
                model="mistral-small",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
            )
            response_content = response.choices[0].message.content
            
            return {
                'response': response_content,
                'papers_in_context': paper_ids,
                'timestamp': datetime.now().isoformat()
            }
            
        except ImportError:
            return {
                'response': "Error: mistralai module not available. Please install with: pip install mistralai",
                'papers_in_context': paper_ids,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'response': f"Error getting AI response: {str(e)}",
                'papers_in_context': paper_ids,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _fetch_paper_details(self, arxiv_id: str) -> Dict:
        """Fetch paper details from arXiv API"""
        try:
            # Clean the arxiv_id to remove any URL encoding issues
            clean_arxiv_id = arxiv_id.replace('%3A', ':').strip()
            
            # Build URL manually to avoid encoding issues
            url = f"{self.base_url}?id_list={clean_arxiv_id}&max_results=1"
            
            response = requests.get(url)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            entry = root.find('{http://www.w3.org/2005/Atom}entry')
            
            if entry is not None:
                paper = {
                    'title': entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
                    'authors': [author.find('{http://www.w3.org/2005/Atom}name').text 
                               for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
                    'abstract': entry.find('{http://www.w3.org/2005/Atom}summary').text.strip(),
                    'published': entry.find('{http://www.w3.org/2005/Atom}published').text,
                    'arxiv_id': arxiv_id,
                    'pdf_url': entry.find('{http://www.w3.org/2005/Atom}id').text.replace('abs', 'pdf'),
                    'categories': [cat.get('term') for cat in entry.findall('{http://arxiv.org/schemas/atom}primary_category')]
                }
                self.paper_context[arxiv_id] = paper
                return paper
            
            return None
        except Exception as e:
            print(f"Error fetching paper details: {e}")
            return None

# Initialize MCP client
mcp_client = ArxivMCPClient()

@cl.on_chat_start
async def start():
    """Initialize the chat session"""
    cl.user_session.set("selected_papers", [])
    cl.user_session.set("search_results", [])
    
    await cl.Message(
        content="🔬 **Welcome to arXiv Paper Chat!**\n\n"
                "I can help you:\n"
                "- 🔍 Search for research papers on arXiv\n"
                "- 📖 Analyze papers with AI\n"
                "- 💬 Have conversations about research\n\n"
                "**Commands:**\n"
                "- `/search <query>` - Search for papers\n"
                "- `/select <number>` - Select a paper from search results\n"
                "- `/papers` - View selected papers\n"
                "- `/analyze <paper_id>` - Analyze a specific paper\n"
                "- Just chat normally to discuss selected papers!\n\n"
                "Try: `/search neural machine translation`"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle user messages"""
    content = message.content.strip()
    
    # Handle commands
    if content.startswith('/search '):
        await handle_search(content[8:])
    elif content.startswith('/select '):
        await handle_select(content[8:])
    elif content == '/papers':
        await handle_show_papers()
    elif content.startswith('/analyze '):
        await handle_analyze(content[9:])
    else:
        # Regular chat about papers
        await handle_chat(content)

async def handle_search(query: str):
    """Handle paper search"""
    if not query.strip():
        await cl.Message(content="❌ Please provide a search query. Example: `/search attention mechanisms`").send()
        return
    
    # Show loading message
    loading_msg = cl.Message(content="🔍 Searching arXiv papers...")
    await loading_msg.send()
    
    try:
        # Search papers
        papers = await mcp_client.search_papers(query, max_results=5)
        
        if not papers:
            await loading_msg.remove()
            await cl.Message(content="❌ No papers found. Try a different search query.").send()
            return
        
        # Store search results
        cl.user_session.set("search_results", papers)
        
        # Format results
        results_text = f"📚 **Found {len(papers)} papers for '{query}':**\n\n"
        
        for i, paper in enumerate(papers, 1):
            authors_str = ", ".join(paper['authors'][:3])
            if len(paper['authors']) > 3:
                authors_str += f" et al."
            
            results_text += f"**{i}. {paper['title']}**\n"
            results_text += f"👥 *{authors_str}*\n"
            results_text += f"🆔 `{paper['arxiv_id']}`\n"
            results_text += f"📅 {paper['published'][:10]}\n"
            results_text += f"📝 {paper['abstract'][:200]}...\n\n"
        
        results_text += "💡 Use `/select <number>` to add papers to your chat context!"
        
        await loading_msg.remove()
        await cl.Message(content=results_text).send()
        
    except Exception as e:
        await loading_msg.remove()
        await cl.Message(content=f"❌ Error searching papers: {str(e)}").send()

async def handle_select(selection: str):
    """Handle paper selection"""
    try:
        paper_num = int(selection.strip())
        search_results = cl.user_session.get("search_results", [])
        
        if not search_results:
            await cl.Message(content="❌ No search results available. Please search for papers first.").send()
            return
        
        if paper_num < 1 or paper_num > len(search_results):
            await cl.Message(content=f"❌ Invalid selection. Please choose a number between 1 and {len(search_results)}.").send()
            return
        
        # Add paper to selected papers
        selected_papers = cl.user_session.get("selected_papers", [])
        paper = search_results[paper_num - 1]
        
        # Check if already selected
        if any(p['arxiv_id'] == paper['arxiv_id'] for p in selected_papers):
            await cl.Message(content=f"ℹ️ Paper '{paper['title']}' is already selected.").send()
            return
        
        selected_papers.append(paper)
        cl.user_session.set("selected_papers", selected_papers)
        
        await cl.Message(
            content=f"✅ **Added to chat context:**\n"
                   f"📄 {paper['title']}\n"
                   f"🆔 {paper['arxiv_id']}\n\n"
                   f"You now have {len(selected_papers)} paper(s) selected. Start chatting about them!"
        ).send()
        
    except ValueError:
        await cl.Message(content="❌ Please provide a valid number. Example: `/select 1`").send()

async def handle_show_papers():
    """Show selected papers"""
    selected_papers = cl.user_session.get("selected_papers", [])
    
    if not selected_papers:
        await cl.Message(content="📭 No papers selected yet. Use `/search` to find papers and `/select` to add them.").send()
        return
    
    papers_text = f"📚 **Selected Papers ({len(selected_papers)}):**\n\n"
    
    for i, paper in enumerate(selected_papers, 1):
        authors_str = ", ".join(paper['authors'][:2])
        if len(paper['authors']) > 2:
            authors_str += " et al."
        
        papers_text += f"**{i}. {paper['title']}**\n"
        papers_text += f"👥 {authors_str}\n"
        papers_text += f"🆔 `{paper['arxiv_id']}`\n"
        papers_text += f"📅 {paper['published'][:10]}\n\n"
    
    await cl.Message(content=papers_text).send()

async def handle_analyze(arxiv_id: str):
    """Handle paper analysis"""
    if not arxiv_id.strip():
        await cl.Message(content="❌ Please provide an arXiv ID. Example: `/analyze 2203.14263v1`").send()
        return
    
    # Clean the arxiv_id to handle any encoding issues
    clean_arxiv_id = arxiv_id.replace('%3A', ':').strip()
    print(f"Analyzing paper: original='{arxiv_id}', cleaned='{clean_arxiv_id}'")
    
    loading_msg = cl.Message(content=f"🤖 Analyzing paper {clean_arxiv_id}...")
    await loading_msg.send()
    
    try:
        analysis = await mcp_client.analyze_paper(clean_arxiv_id)
        
        analysis_text = f"📊 **Analysis of {clean_arxiv_id}:**\n\n"
        analysis_text += analysis['analysis']
        
        await loading_msg.remove()
        await cl.Message(content=analysis_text).send()
        
    except Exception as e:
        await loading_msg.remove()
        await cl.Message(content=f"❌ Error analyzing paper: {str(e)}").send()

async def handle_chat(message: str):
    """Handle regular chat about papers"""
    selected_papers = cl.user_session.get("selected_papers", [])
    
    if not selected_papers:
        await cl.Message(
            content="💡 **No papers selected for chat context.**\n\n"
                   "Please:\n"
                   "1. Search for papers: `/search <query>`\n"
                   "2. Select papers: `/select <number>`\n"
                   "3. Then chat about them!"
        ).send()
        return
    
    # Show typing indicator
    loading_msg = cl.Message(content="🤖 Thinking about your question...")
    await loading_msg.send()
    
    try:
        paper_ids = [paper['arxiv_id'] for paper in selected_papers]
        response = await mcp_client.chat_about_papers(message, paper_ids)
        
        chat_response = f"🤖 **AI Response:**\n\n{response['response']}\n\n"
        chat_response += f"📚 *Based on {len(paper_ids)} selected paper(s)*"
        
        await loading_msg.remove()
        await cl.Message(content=chat_response).send()
        
    except Exception as e:
        await loading_msg.remove()
        await cl.Message(content=f"❌ Error getting AI response: {str(e)}").send()

if __name__ == "__main__":
    cl.run()