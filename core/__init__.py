"""Core functionality package"""
from .browser import BrowserManager
from .session import SessionManager
from .anti_detection import AntiDetection

__all__ = ['BrowserManager', 'SessionManager', 'AntiDetection']
