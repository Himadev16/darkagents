"""
DARKAGENTS Agents Package
11 specialized AI agents for building SaaS applications
"""
from backend.agents.base_agent import BaseAgent
from backend.agents.product_manager import ProductManagerAgent

__all__ = [
    "BaseAgent",
    "ProductManagerAgent",
]