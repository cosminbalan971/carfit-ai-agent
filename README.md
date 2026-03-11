# carfit-ai-agent

CarFit is a hybrid AI agent that recommends cars through a conversational interface.  
It combines **LLM-based conversation understanding** with a **deterministic scoring engine** to produce reliable and explainable recommendations.

The project explores how AI agents can blend natural language interaction with structured reasoning systems.

#LIVE DEMO: https://carfit-ai-agent.onrender.com/ui

---

# Features

• Conversational chat interface for car discovery  
• LLM conversation router for natural interactions  
• Deterministic car scoring engine  
• Preference inference from natural language  
• Session memory across turns  
• Fallback policy when no matches are found  
• Explainable recommendations  

Example interaction:

User: I want a quiet sedan under 18k
Agent: Based on your preferences I found two strong options: Honda Civic (2019+) and Mazda 6 (2018+)

# Architecture

The system uses a **hybrid AI architecture**.
User -> Chat UI -> Conversation Router (LLM) -> Preference Extraction ->Deterministic Recommendation Engine -> LLM Explanation Layer -> Final Response

This allows the agent to remain conversational while keeping recommendations grounded in deterministic logic.

---

# Tech Stack

Backend
- Python
- FastAPI

AI
- OpenAI API
- LLM conversation routing

Frontend
- Minimal chat UI (HTML / JS / CSS)

Data
- JSON dataset of car specifications

---
