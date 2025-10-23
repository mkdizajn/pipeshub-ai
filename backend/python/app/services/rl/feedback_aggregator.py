"""
Feedback Aggregator Service

Collects and processes user feedback from conversations stored in MongoDB.
Provides aggregation, filtering, and export capabilities for RL training.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from .schema import FeedbackAggregation, FeedbackType
from .config import RLConfig, default_rl_config


class FeedbackAggregator:
    """
    Service for aggregating feedback data from conversations.
    
    Reads from existing MongoDB conversation collections and aggregates
    feedback data for analysis and training dataset preparation.
    """
    
    def __init__(self,
        mongodb: AsyncIOMotorDatabase,
        config: Optional[RLConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.mongodb = mongodb
        self.config = config or default_rl_config
        self.logger = logger or logging.getLogger(__name__)
        self.conversations_collection = mongodb.get_collection("conversations")
    
    async def aggregate_feedback(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        min_feedback_count: int = 1
    ) -> FeedbackAggregation:
        """
        Aggregate feedback data with optional filters.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            org_id: Filter by organization ID
            user_id: Filter by user ID
            min_feedback_count: Minimum feedback entries per message
        
        Returns:
            FeedbackAggregation with statistics
        """
        self.logger.info(
            f"Aggregating feedback: start={start_date}, end={end_date}, "
            f"org={org_id}, user={user_id}"
        )
        
        # Build MongoDB query
        query = self._build_query(start_date, end_date, org_id, user_id)
        
        # Initialize counters
        stats = {
            "total_conversations": 0,
            "total_messages": 0,
            "total_feedback_entries": 0,
            "positive_feedback_count": 0,
            "negative_feedback_count": 0,
            "neutral_feedback_count": 0,
            "accuracy_scores": [],
            "relevance_scores": [],
            "completeness_scores": [],
            "clarity_scores": [],
            "citation_relevance_scores": []
        }
        
        # Process conversations
        async for conversation in self.conversations_collection.find(query):
            stats["total_conversations"] += 1
            
            messages = conversation.get("messages", [])
            for message in messages:
                # Skip user queries, only process AI responses
                if message.get("messageType") != "ai_response":
                    continue
                
                feedback_list = message.get("feedback", [])
                if len(feedback_list) < min_feedback_count:
                    continue
                
                stats["total_messages"] += 1
                
                # Process each feedback entry
                for feedback in feedback_list:
                    stats["total_feedback_entries"] += 1
                    
                    # Classify feedback type
                    feedback_type = self._classify_feedback(feedback)
                    if feedback_type == FeedbackType.POSITIVE:
                        stats["positive_feedback_count"] += 1
                    elif feedback_type == FeedbackType.NEGATIVE:
                        stats["negative_feedback_count"] += 1
                    else:
                        stats["neutral_feedback_count"] += 1
                    
                    # Collect rating scores
                    ratings = feedback.get("ratings", {})
                    if ratings.get("accuracy"):
                        stats["accuracy_scores"].append(ratings["accuracy"])
                    if ratings.get("relevance"):
                        stats["relevance_scores"].append(ratings["relevance"])
                    if ratings.get("completeness"):
                        stats["completeness_scores"].append(ratings["completeness"])
                    if ratings.get("clarity"):
                        stats["clarity_scores"].append(ratings["clarity"])
                    
                    # Collect citation feedback
                    citation_feedback = feedback.get("citationFeedback", [])
                    for cf in citation_feedback:
                        if cf.get("relevanceScore"):
                            stats["citation_relevance_scores"].append(cf["relevanceScore"])
        
        # Compute averages
        return FeedbackAggregation(
            total_conversations=stats["total_conversations"],
            total_messages=stats["total_messages"],
            total_feedback_entries=stats["total_feedback_entries"],
            positive_feedback_count=stats["positive_feedback_count"],
            negative_feedback_count=stats["negative_feedback_count"],
            neutral_feedback_count=stats["neutral_feedback_count"],
            avg_accuracy=self._safe_avg(stats["accuracy_scores"]),
            avg_relevance=self._safe_avg(stats["relevance_scores"]),
            avg_completeness=self._safe_avg(stats["completeness_scores"]),
            avg_clarity=self._safe_avg(stats["clarity_scores"]),
            avg_citation_relevance=self._safe_avg(stats["citation_relevance_scores"]),
            start_date=start_date or datetime.min,
            end_date=end_date or datetime.utcnow(),
            org_id=org_id,
            user_id=user_id
        )
    
    async def get_feedback_by_conversation(
        self,
        conversation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all feedback for a specific conversation.
        
        Args:
            conversation_id: Conversation ID
        
        Returns:
            List of feedback entries with message context
        """
        conversation = await self.conversations_collection.find_one(
            {"_id": conversation_id}
        )
        
        if not conversation:
            return []
        
        feedback_data = []
        for message in conversation.get("messages", []):
            if message.get("messageType") != "ai_response":
                continue
            
            for feedback in message.get("feedback", []):
                feedback_data.append({
                    "message_id": str(message.get("_id")),
                    "message_content": message.get("content"),
                    "feedback": feedback,
                    "created_at": message.get("createdAt")
                })
        
        return feedback_data
    
    def _build_query(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        org_id: Optional[str],
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Build MongoDB query with filters"""
        query = {"isDeleted": False}
        
        if org_id:
            query["orgId"] = org_id
        if user_id:
            query["userId"] = user_id
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["createdAt"] = date_filter
        
        return query
    
    def _classify_feedback(self, feedback: Dict[str, Any]) -> FeedbackType:
        """
        Classify feedback as positive, negative, or neutral.
        
        Args:
            feedback: Feedback dictionary
        
        Returns:
            FeedbackType enum
        """
        is_helpful = feedback.get("isHelpful")
        
        # Check explicit helpful flag
        if is_helpful is True:
            return FeedbackType.POSITIVE
        elif is_helpful is False:
            return FeedbackType.NEGATIVE
        
        # Check ratings if available
        ratings = feedback.get("ratings", {})
        if ratings:
            avg_rating = sum(ratings.values()) / len(ratings)
            if avg_rating >= 4.0:
                return FeedbackType.POSITIVE
            elif avg_rating <= 2.0:
                return FeedbackType.NEGATIVE
        
        return FeedbackType.NEUTRAL
    
    @staticmethod
    def _safe_avg(values: List[float]) -> Optional[float]:
        """Safely compute average, returning None for empty lists"""
        return sum(values) / len(values) if values else None
