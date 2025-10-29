"""
DARKAGENTS Agents Package
11 specialized AI agents for building SaaS applications
"""
from backend.agents.base_agent import BaseAgent
from backend.agents.product_manager import ProductManagerAgent
from backend.agents.polyglot_agent import PolyglotAgent
from backend.agents.system_architect_agent import SystemArchitectAgent
from backend.agents.ui_ux_designer_agent import UIUXDesignerAgent
from backend.agents.qa_engineer_agent import QAEngineerAgent

__all__ = [
    "BaseAgent",
    "ProductManagerAgent",
    "PolyglotAgent",
    "SystemArchitectAgent",
    "UIUXDesignerAgent",
    "QAEngineerAgent",
]