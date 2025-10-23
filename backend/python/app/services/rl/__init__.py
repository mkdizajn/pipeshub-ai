"""
Reinforcement Learning Module for PipesHub AI

This module provides infrastructure for Reinforcement Learning from Human Feedback (RLHF),
including feedback aggregation, reward computation, dataset building, and metrics tracking.

Phase 1: Foundation - Data collection and analysis without modifying existing functionality
"""

from .feedback_aggregator import FeedbackAggregator
from .reward_model import RewardModel
from .dataset_builder import DatasetBuilder
from .metrics_tracker import MetricsTracker

__all__ = [
    "FeedbackAggregator",
    "RewardModel", 
    "DatasetBuilder",
    "MetricsTracker",
]

__version__ = "1.0.0-phase1"
