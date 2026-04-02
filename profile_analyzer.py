"""
Profile Analyzer Module.

Provides basic (non-AI) profile analysis for quick validation
and completeness checking before sending to the AI for deep analysis.
This serves as a pre-processing step and fallback.
"""


class ProfileAnalyzer:
    """Performs basic profile validation and completeness analysis."""
    
    # Minimum recommended lengths for each section
    RECOMMENDED_LENGTHS = {
        "headline": {"min": 20, "max": 220, "ideal_min": 50},
        "summary": {"min": 100, "max": 2600, "ideal_min": 300},
        "experience_item": {"min": 50, "ideal_min": 150},
    }
    
    # Common weak words that should be avoided
    WEAK_WORDS = [
        "responsible for", "duties include", "helped", "worked on",
        "assisted", "participated", "involved in", "team player",
        "hard worker", "detail-oriented", "passionate", "guru",
        "ninja", "rockstar", "self-starter"
    ]
    
    # Strong action verbs for experience bullets
    STRONG_VERBS = [
        "achieved", "accelerated", "built", "created", "delivered",
        "designed", "developed", "drove", "engineered", "established",
        "executed", "generated", "grew", "implemented", "improved",
        "increased", "initiated", "launched", "led", "managed",
        "negotiated", "optimized", "orchestrated", "pioneered",
        "reduced", "redesigned", "scaled", "secured", "spearheaded",
        "streamlined", "transformed"
    ]
    
    @staticmethod
    def validate_profile(profile_data: dict) -> dict:
        """
        Validate that profile data has required fields.
        
        Args:
            profile_data: Raw profile data from user input
            
        Returns:
            Validation result with any missing fields
        """
        required_fields = ["name", "headline"]
        optional_fields = ["summary", "experience", "skills", "industry",
                          "target_role"]
        
        missing_required = []
        missing_optional = []
        
        for field in required_fields:
            if not profile_data.get(field):
                missing_required.append(field)
        
        for field in optional_fields:
            if not profile_data.get(field):
                missing_optional.append(field)
        
        is_valid = len(missing_required) == 0
        
        return {
            "is_valid": is_valid,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "message": (
                "Profile data is valid." if is_valid 
                else f"Missing required fields: {', '.join(missing_required)}"
            )
        }
    
    @staticmethod
    def quick_completeness_score(profile_data: dict) -> dict:
        """
        Calculate a quick completeness score without AI.
        
        This gives instant feedback while the AI analysis is processing.
        
        Args:
            profile_data: Profile data dictionary
            
        Returns:
            Completeness score and breakdown
        """
        scores = {}
        
        # Score headline (0-15 points)
        headline = profile_data.get("headline", "")
        headline_score = 0
        if headline:
            headline_score += 5  # Has content
            if len(headline) >= 50:
                headline_score += 5  # Decent length
            if "|" in headline or "•" in headline or "—" in headline:
                headline_score += 3  # Has separators (structured)
            if len(headline) > 220:
                headline_score -= 3  # Too long
            headline_score += 2  # Participation points
        scores["headline"] = min(15, max(0, headline_score))
        
        # Score summary (0-25 points)
        summary = profile_data.get("summary", "")
        summary_score = 0
        if summary:
            summary_score += 5
            if len(summary) >= 300:
                summary_score += 5
            if len(summary) >= 1000:
                summary_score += 5
            if any(char.isdigit() for char in summary):
                summary_score += 3  # Contains metrics
            if "\n" in summary:
                summary_score += 3  # Has formatting
            summary_score += 4
        scores["summary"] = min(25, max(0, summary_score))
        
        # Score experience (0-35 points)
        experience = profile_data.get("experience", [])
        exp_score = 0
        if experience:
            exp_score += 5  # Has experience
            exp_score += min(10, len(experience) * 3)  # Points per entry
            
            for exp in experience:
                desc = exp.get("description", "")
                if len(desc) >= 100:
                    exp_score += 3
                if any(char.isdigit() for char in desc):
                    exp_score += 2  # Contains metrics
        scores["experience"] = min(35, max(0, exp_score))
        
        # Score skills (0-15 points)
        skills = profile_data.get("skills", [])
        skills_score = 0
        if skills:
            skills_score += 5
            skills_score += min(10, len(skills))
        scores["skills"] = min(15, max(0, skills_score))
        
        # Bonus for additional info (0-10 points)
        bonus = 0
        if profile_data.get("industry"):
            bonus += 3
        if profile_data.get("target_role"):
            bonus += 3
        if profile_data.get("education"):
            bonus += 4
        scores["bonus"] = min(10, bonus)
        
        total = sum(scores.values())
        
        return {
            "total_score": total,
            "max_score": 100,
            "percentage": total,
            "breakdown": scores,
            "level": (
                "Beginner" if total < 30 
                else "Intermediate" if total < 60 
                else "Advanced" if total < 80 
                else "All-Star"
            )
        }
    
    @classmethod
    def find_weak_words(cls, text: str) -> list:
        """
        Find weak words/phrases in the given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of found weak words
        """
        text_lower = text.lower()
        found = []
        for word in cls.WEAK_WORDS:
            if word in text_lower:
                found.append(word)
        return found