"""
Carnatic Music Learning Platform - Core Module

This module contains the core business logic, models, services, and utilities
for the Carnatic music learning application.
"""

from .ml import adaptive_engine
from .models import shruti, user

__all__ = ["shruti", "user", "adaptive_engine"]
