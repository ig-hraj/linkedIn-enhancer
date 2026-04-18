"""
AI Service Layer for LinkedIn Enhancement Tool.

This module handles all communication with the Google Gemini API.
It constructs prompts, manages conversation context, and parses responses.
"""

import json
import re
import google.generativeai as genai
from config import Config
from prompts import (
    CHATBOT_SYSTEM_PROMPT,
    PROFILE_ANALYSIS_PROMPT,
    SECTION_REWRITE_PROMPT,
    SECTION_GUIDELINES,
    CHAT_WITH_PROFILE_CONTEXT,
    CONTENT_ANALYSIS_PROMPT,
    COMMENT_SUGGESTION_PROMPT,
    POST_SUMMARY_PROMPT
)


class AIService:
    """Handles all AI-related operations using Google Gemini API."""
    
    def __init__(self):
        """Initialize the AI service with Gemini API configuration."""
        # Configure the Gemini API with our key
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Initialize the generative model, try configured and fallback models
        self.model = None
        candidate_models = [
            Config.AI_MODEL,
            "gemini-flash-lite-latest",
            "gemini-flash-latest",
            "gemini-2.5-flash",
            "gemini-2.0-flash"
        ]

        for model_name in candidate_models:
            if not model_name:
                continue
            try:
                self.model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={
                        "temperature": Config.TEMPERATURE,
                        "max_output_tokens": Config.MAX_TOKENS,
                        "top_p": 0.95,
                    }
                )
                print(f"AI Service: using model {model_name}")
                break
            except Exception as e:
                print(f"AI Service: failed to initialize model {model_name}: {e}")

        if not self.model:
            raise RuntimeError("Unable to initialize any Gemini model. Check model names/quota.")

        # Store conversation histories for different chat sessions
        # Key: session_id, Value: list of message dicts
        self.conversations = {}
    
    def analyze_profile(self, profile_data: dict) -> dict:
        """
        Analyze a LinkedIn profile and return scored evaluation.
        
        Args:
            profile_data: Dictionary containing profile sections
            
        Returns:
            Dictionary with scores, assessments, and suggestions
        """
        # Build the analysis prompt by injecting profile data
        prompt = PROFILE_ANALYSIS_PROMPT.format(
            profile_json=json.dumps(profile_data, indent=2),
            headline=profile_data.get("headline", "Not provided"),
            summary=profile_data.get("summary", "Not provided"),
            experience_count=len(profile_data.get("experience", [])),
            skills_list=", ".join(profile_data.get("skills", ["None listed"]))
        )
        
        try:
            # Send to Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response — remove markdown code blocks if present
            response_text = self._clean_json_response(response_text)
            
            # Parse the JSON response
            analysis = json.loads(response_text)
            return {"success": True, "analysis": analysis}
            
        except json.JSONDecodeError as e:
            # If AI didn't return valid JSON, try to extract it
            print(f"JSON parse error: {e}")
            print(f"Raw response: {response_text[:500]}")
            return {
                "success": False,
                "error": "Failed to parse AI response. Please try again.",
                "raw_response": response_text[:1000]
            }
        except Exception as e:
            print(f"AI Service Error: {e}")
            return {
                "success": False,
                "error": f"AI service error: {str(e)}"
            }
    
    def rewrite_section(self, section_name: str, current_content: str, 
                        context: dict) -> dict:
        """
        Generate improved versions of a profile section.
        
        Args:
            section_name: Which section to rewrite (headline, summary, etc.)
            current_content: The current text of that section
            context: Additional context (industry, target role, etc.)
            
        Returns:
            Dictionary with 3 rewritten versions
        """
        # Get section-specific guidelines
        guidelines = SECTION_GUIDELINES.get(
            section_name.lower(), 
            "Improve clarity, impact, and keyword optimization."
        )
        
        # Build the rewrite prompt
        prompt = SECTION_REWRITE_PROMPT.format(
            section_name=section_name.upper(),
            current_content=current_content,
            industry=context.get("industry", "Not specified"),
            target_role=context.get("target_role", "Not specified"),
            experience_years=context.get("experience_years", "Not specified"),
            key_skills=", ".join(context.get("key_skills", ["Not specified"])),
            section_specific_guidelines=guidelines
        )
        
        try:
            response = self.model.generate_content(prompt)
            response_text = self._clean_json_response(response.text.strip())
            
            result = json.loads(response_text)
            return {"success": True, "rewrites": result}
            
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse rewrite suggestions. Please try again."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Rewrite service error: {str(e)}"
            }
    
    def chat(self, session_id: str, user_message: str, 
             profile_data: dict = None) -> dict:
        """
        Handle a chatbot conversation turn.
        
        Args:
            session_id: Unique identifier for this conversation
            user_message: The user's message
            profile_data: Optional profile data for personalized advice
            
        Returns:
            Dictionary with the AI's response
        """
        # Initialize conversation history if new session
        if session_id not in self.conversations:
            self.conversations[session_id] = []
            
            # Build system context with profile data if available
            system_context = CHATBOT_SYSTEM_PROMPT
            if profile_data:
                system_context += "\n" + CHAT_WITH_PROFILE_CONTEXT.format(
                    name=profile_data.get("name", "User"),
                    headline=profile_data.get("headline", "Not provided"),
                    summary=profile_data.get("summary", "Not provided"),
                    experience=json.dumps(
                        profile_data.get("experience", []), indent=2
                    ),
                    skills=", ".join(profile_data.get("skills", [])),
                    industry=profile_data.get("industry", "Not specified")
                )
            
            # Store system prompt as first message
            self.conversations[session_id].append({
                "role": "system",
                "content": system_context
            })
        
        # Add user message to history
        self.conversations[session_id].append({
            "role": "user",
            "content": user_message
        })
        
        try:
            # Build the full conversation for Gemini
            # Gemini uses a different format — we'll construct a single prompt
            # that includes conversation history
            full_prompt = self._build_conversation_prompt(session_id)
            
            response = self.model.generate_content(full_prompt)
            assistant_message = response.text.strip()
            
            # Store assistant response in history
            self.conversations[session_id].append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Keep conversation history manageable (last 20 turns)
            if len(self.conversations[session_id]) > 42:  # system + 20 pairs
                system_msg = self.conversations[session_id][0]
                self.conversations[session_id] = (
                    [system_msg] + self.conversations[session_id][-20:]
                )
            
            return {
                "success": True,
                "response": assistant_message,
                "session_id": session_id
            }
            
        except Exception as e:
            print(f"Chat error: {e}")
            return {
                "success": False,
                "error": f"Chat service error: {str(e)}"
            }
    
    def _build_conversation_prompt(self, session_id: str) -> str:
        """
        Build a full conversation prompt from history for Gemini.
        
        Gemini doesn't natively support chat history in the same way as
        OpenAI, so we format the conversation into a single prompt.
        """
        messages = self.conversations[session_id]
        prompt_parts = []
        
        for msg in messages:
            if msg["role"] == "system":
                prompt_parts.append(
                    f"SYSTEM INSTRUCTIONS:\n{msg['content']}\n"
                )
            elif msg["role"] == "user":
                prompt_parts.append(f"USER: {msg['content']}")
            elif msg["role"] == "assistant":
                prompt_parts.append(f"ASSISTANT: {msg['content']}")
        
        prompt_parts.append("ASSISTANT:")
        return "\n\n".join(prompt_parts)
    
    def _clean_json_response(self, text: str) -> str:
        """
        Clean AI response to extract valid JSON.
        
        The AI sometimes wraps JSON in markdown code blocks
        or adds explanatory text. This method handles that.
        """
        # Remove markdown code block markers
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()
        
        # Try to find JSON object in the text
        if not text.startswith('{'):
            # Try to find the first { and last }
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                text = text[start:end + 1]
        
        return text
    
    def clear_conversation(self, session_id: str) -> bool:
        """Clear a conversation's history."""
        if session_id in self.conversations:
            del self.conversations[session_id]
            return True
        return False

    def analyze_content(self, content: str, author_info: dict,
                        content_type: str = "post") -> dict:
        """
        Analyze tone, intent, and audience of LinkedIn content.

        Args:
            content: The text content to analyze
            author_info: Information about the content author
            content_type: Type of content (post, article, comment)

        Returns:
            Dictionary with tone, intent, audience analysis
        """
        prompt = CONTENT_ANALYSIS_PROMPT.format(
            content=content,
            author_info=json.dumps(author_info) if author_info else "Not available",
            content_type=content_type
        )

        try:
            response = self.model.generate_content(prompt)
            response_text = self._clean_json_response(response.text.strip())
            analysis = json.loads(response_text)
            return {"success": True, "analysis": analysis}
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse content analysis. Please try again."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Content analysis error: {str(e)}"
            }

    def generate_comments(self, post_content: str, analysis: dict,
                          user_profile: dict = None) -> dict:
        """
        Generate contextual comment suggestions for a LinkedIn post.

        Args:
            post_content: The post text to generate comments for
            analysis: Content analysis results (tone, intent, etc.)
            user_profile: Optional commenter profile for personalization

        Returns:
            Dictionary with 4 comment suggestions in different styles
        """
        prompt = COMMENT_SUGGESTION_PROMPT.format(
            post_content=post_content,
            tone=analysis.get("tone", {}).get("primary", "unknown"),
            intent=analysis.get("intent", {}).get("primary", "unknown"),
            topics=", ".join(analysis.get("key_topics", ["general"])),
            user_context=json.dumps(user_profile) if user_profile else "Not provided"
        )

        try:
            response = self.model.generate_content(prompt)
            response_text = self._clean_json_response(response.text.strip())
            comments = json.loads(response_text)
            return {"success": True, "suggestions": comments}
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse comment suggestions. Please try again."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Comment generation error: {str(e)}"
            }

    def summarize_post(self, post_content: str) -> dict:
        """
        Generate a quick 2-sentence summary of a LinkedIn post.

        Args:
            post_content: The post text to summarize

        Returns:
            Dictionary with the summary text
        """
        prompt = POST_SUMMARY_PROMPT.format(post_content=post_content)

        try:
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            return {"success": True, "summary": summary}
        except Exception as e:
            return {
                "success": False,
                "error": f"Summarization error: {str(e)}"
            }