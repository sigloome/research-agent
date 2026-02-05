

class UserProfile:
    """
    Manages user preferences using a lightweight learning mechanism (Bandit-lite).
    """
    def __init__(self):
        # Feature weights for different preferences
        self.preferences = {
            "language": {
                "C++": 0.5,
                "Python": 0.5
            },
            "verbosity": {
                "detailed": 0.5,
                "concise": 0.5
            }
        }
        
    def update_preference(self, category: str, item: str, reward: float = 1.0):
        """
        Updates the weight of a preference based on feedback (reward).
        Reward should be positive for 'likes/usage' and negative for 'corrections'.
        """
        if category not in self.preferences:
            self.preferences[category] = {}
        
        # Simple additive update (like a Bandit count or score)
        current = self.preferences[category].get(item, 0.5)
        self.preferences[category][item] = current + reward
        
        print(f"[Learning] Updated {category}:{item} score to {self.preferences[category][item]}")

    def get_preferred_option(self, category: str) -> str:
        """Returns the highest scoring option for a category."""
        if category not in self.preferences:
            return None
        
        # Return key with max value
        options = self.preferences[category]
        return max(options, key=options.get)

class LearningAgent:
    """
    An agent that learns from user interactions.
    """
    def __init__(self):
        self.profile = UserProfile()
        
    def process_turn(self, user_input: str) -> str:
        # 1. Implicit Feedback Detection (Simulated)
        if "hate C++" in user_input or "meant in Python" in user_input:
            # Negative feedback for C++, Positive for Python
            self.profile.update_preference("language", "C++", -0.5)
            self.profile.update_preference("language", "Python", 1.0)
            return "Learned: You prefer Python over C++."
            
        # 2. Decision Making based on Profile
        preferred_lang = self.profile.get_preferred_option("language")
        
        if "sort" in user_input or "reverse" in user_input:
             return f"Here is the {preferred_lang} code example..."
             
        return "I'm listening."
