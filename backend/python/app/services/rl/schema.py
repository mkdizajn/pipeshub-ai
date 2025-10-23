"""
Schema Definitions for RL Module

Pydantic models for RL service data structures.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    """Classification of feedback sentiment"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class FeedbackAggregation(BaseModel):
    """Aggregated feedback statistics"""
    
    total_conversations: int = Field(description="Number of conversations processed")
    total_messages: int = Field(description="Number of AI messages with feedback")
    total_feedback_entries: int = Field(description="Total feedback entries")
    
    positive_feedback_count: int = Field(description="Count of positive feedback")
    negative_feedback_count: int = Field(description="Count of negative feedback")
    neutral_feedback_count: int = Field(description="Count of neutral feedback")
    
    avg_accuracy: Optional[float] = Field(default=None, description="Average accuracy rating")
    avg_relevance: Optional[float] = Field(default=None, description="Average relevance rating")
    avg_completeness: Optional[float] = Field(default=None, description="Average completeness rating")
    avg_clarity: Optional[float] = Field(default=None, description="Average clarity rating")
    avg_citation_relevance: Optional[float] = Field(default=None, description="Average citation relevance")
    
    start_date: datetime = Field(description="Start of aggregation period")
    end_date: datetime = Field(description="End of aggregation period")
    org_id: Optional[str] = Field(default=None, description="Organization filter")
    user_id: Optional[str] = Field(default=None, description="User filter")
    
    @property
    def positive_rate(self) -> float:
        """Calculate positive feedback rate"""
        if self.total_feedback_entries == 0:
            return 0.0
        return self.positive_feedback_count / self.total_feedback_entries
    
    @property
    def negative_rate(self) -> float:
        """Calculate negative feedback rate"""
        if self.total_feedback_entries == 0:
            return 0.0
        return self.negative_feedback_count / self.total_feedback_entries


class RewardSignal(BaseModel):
    """Computed reward signal for a message"""
    
    message_id: str = Field(description="Message ID")
    conversation_id: str = Field(description="Conversation ID")
    
    reward_score: float = Field(ge=-1.0, le=1.0, description="Composite reward score [-1, 1]")
    
    # Component scores
    ratings_component: Optional[float] = Field(default=None, description="Ratings contribution")
    binary_component: Optional[float] = Field(default=None, description="Binary feedback contribution")
    citation_component: Optional[float] = Field(default=None, description="Citation feedback contribution")
    time_component: Optional[float] = Field(default=None, description="Time factor contribution")
    
    # Metadata
    feedback_count: int = Field(description="Number of feedback entries")
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    
    explanation: Optional[str] = Field(default=None, description="Human-readable explanation")


class TrainingDatasetMetadata(BaseModel):
    """Metadata for a training dataset"""
    
    dataset_id: str = Field(description="Unique dataset identifier")
    version: str = Field(description="Dataset version")
    
    total_examples: int = Field(description="Total number of examples")
    positive_examples: int = Field(description="Positive examples count")
    negative_examples: int = Field(description="Negative examples count")
    
    train_count: int = Field(description="Training set size")
    validation_count: int = Field(description="Validation set size")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    config: Dict[str, Any] = Field(description="Dataset configuration used")
    
    # Filters applied
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    org_id: Optional[str] = Field(default=None)


class MetricsSummary(BaseModel):
    """Summary statistics for a time period"""
    
    period_start: datetime = Field(description="Start of metrics period")
    period_end: datetime = Field(description="End of metrics period")
    
    # Volume metrics
    total_conversations: int
    total_messages: int
    total_feedback_entries: int
    
    # Quality metrics
    avg_reward_score: Optional[float] = Field(default=None)
    avg_accuracy: Optional[float] = Field(default=None)
    avg_relevance: Optional[float] = Field(default=None)
    avg_completeness: Optional[float] = Field(default=None)
    avg_clarity: Optional[float] = Field(default=None)
    
    # Distribution
    positive_rate: float
    negative_rate: float
    neutral_rate: float
    
    # Percentiles
    reward_percentiles: Optional[Dict[str, float]] = Field(default=None)


class TimeSeriesMetric(BaseModel):
    """Time-series data point"""
    
    timestamp: datetime
    metric_name: str
    metric_value: float
    metadata: Optional[Dict[str, Any]] = Field(default=None)