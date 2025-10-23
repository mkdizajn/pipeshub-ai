class RewardModel:
    def __init__(self, weights):
        """
        Initializes the RewardModel with configurable weights.
        
        Args:
            weights (dict): A dictionary of weights for each feedback type.
        """
        self.weights = weights

    def compute_reward(self, feedback):
        """
        Computes the composite reward signal based on user feedback.
        
        Args:
            feedback (dict): A dictionary containing user feedback data.
        
        Returns:
            float: The computed reward signal.
        """
        reward_signal = 0.0
        for feedback_type, value in feedback.items():
            weight = self.weights.get(feedback_type, 0)
            reward_signal += weight * value
        return reward_signal
