"""Configuration package"""
from .settings import config, ScraperConfig, URLConfig, SelectorConfig
from .user_agents import UserAgentPool

__all__ = ['config', 'ScraperConfig', 'URLConfig', 'SelectorConfig', 'UserAgentPool']
