"""
Configuration for RL Module

Defines configurable parameters for reward computation, dataset building,
and metrics tracking.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class RewardWeights(BaseModel):
    """Weights for computing composite reward signals"""
    
    ratings_weight: float = Field(default=0.4, ge=0.0, le=1.0, description="Weight for user ratings")
    binary_feedback_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Weight for thumbs up/down")
    citation_feedback_weight: float = Field(default=0.2, ge=0.0, le=1.0, description="Weight for citation quality")
    time_factor_weight: float = Field(default=0.1, ge=0.0, le=1.0, description="Weight for time-to-feedback")
    
    def validate_sum(self) -> bool:
        """Ensure weights sum to 1.0"""
        total = (
            self.ratings_weight + 
            self.binary_feedback_weight + 
            self.citation_feedback_weight + 
            self.time_factor_weight
        )
        return abs(total - 1.0) < 0.001


class DatasetConfig(BaseModel):
    """Configuration for dataset building"""
    
    train_split: float = Field(default=0.8, ge=0.0, le=1.0, description="Training set proportion")
    min_feedback_count: int = Field(default=1, ge=1, description="Minimum feedback required per conversation")
    max_response_length: int = Field(default=4096, ge=100, description="Maximum response length in characters")
    include_neutral: bool = Field(default=True, description="Include neutral feedback in dataset")
    format: str = Field(default="json", description="Output format: json, parquet, or huggingface")


class MetricsConfig(BaseModel):
    """Configuration for metrics tracking"""
    
    aggregation_window_days: int = Field(default=7, ge=1, description="Days to aggregate metrics over")
    percentiles: list[float] = Field(default=[0.25, 0.5, 0.75, 0.95], description="Percentiles for distribution")
    cache_ttl_seconds: int = Field(default=300, ge=0, description="Cache TTL for metrics")


class RLConfig(BaseModel):
    """Main RL module configuration"""
    
    reward_weights: RewardWeights = Field(default_factory=RewardWeights)
    dataset_config: DatasetConfig = Field(default_factory=DatasetConfig)
    metrics_config: MetricsConfig = Field(default_factory=MetricsConfig)
    
    # Storage paths
    dataset_output_path: str = Field(default="/data/rl/datasets", description="Path for storing datasets")
    model_output_path: str = Field(default="/data/rl/models", description="Path for storing trained models")
    
    # Feature flags
    enable_reward_caching: bool = Field(default=True, description="Cache computed rewards")
    enable_metrics_tracking: bool = Field(default=True, description="Track metrics over time")
    
    # Database collections
    training_dataset_collection: str = Field(default="rl_training_datasets")
    reward_model_collection: str = Field(default="rl_reward_models")
    metrics_collection: str = Field(default="rl_metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reward_weights": {
                    "ratings_weight": 0.4,
                    "binary_feedback_weight": 0.3,
                    "citation_feedback_weight": 0.2,
                    "time_factor_weight": 0.1
                },
                "dataset_config": {
                    "train_split": 0.8,
                    "min_feedback_count": 1,
                    "format": "json"
                }
            }
        }


# Default configuration instance
default_rl_config = RLConfig()