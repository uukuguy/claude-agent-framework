"""
Centralized type definitions for Claude Agent Framework.

This module provides all public type aliases and enums used throughout the framework.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

__all__ = ["ModelType", "ModelTypeStr", "ArchitectureType"]


# Architecture types
ArchitectureType = Literal[
    "research",
    "pipeline",
    "critic_actor",
    "specialist_pool",
    "debate",
    "reflexion",
    "mapreduce",
]


# Model type as Enum (canonical, for Pydantic)
class ModelType(str, Enum):
    """Supported Claude model types."""

    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


# Model type as Literal (for init() backward compat)
ModelTypeStr = Literal["haiku", "sonnet", "opus"]
