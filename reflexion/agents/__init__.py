"""多智能体模块 - 实现多个Agent协作"""

from reflexion.agents.collaboration import CollaborativeAgents
from reflexion.agents.specialized import PlannerAgent, ExecutorAgent, CriticAgent

__all__ = [
    "CollaborativeAgents",
    "PlannerAgent",
    "ExecutorAgent",
    "CriticAgent",
]
