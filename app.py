"""
LinkedIn Enhancement Tool — Flask Application.

Main entry point for the backend server.
Defines all API routes and handles request/response processing.
"""

import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
from ai_service import AIService
from profile_analyzer import ProfileAnalyzer
import json
import requests
from bs4 import BeautifulSoup

# ============================================================
# App Initialization
# ============================================================

# Validate configuration before starting, but do not hard-crash the process.
# Render should keep the web worker alive even when the AI key is missing so
# the app can still show a clear runtime error instead of a startup failure.
try:
    Config.validate()
    config_error = None
except Exception as exc:
    config_error = str(exc)
    print(f"⚠️  Configuration warning: {config_error}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Create Flask app
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)  # Enable CORS for frontend-backend communication

# Initialize services
try:
    ai_service = AIService()
except Exception as exc:
    ai_service = None
    print(f"⚠️  AI service disabled: {exc}")
analyzer = ProfileAnalyzer()


def _require_ai_service():
    if ai_service is None:
        return jsonify({
            "success": False,
            "error": "AI service is unavailable. Check GEMINI_API_KEY and deployment env vars."
        }), 503
    return None


def _build_empty_profile():
    return {
        "name": "",
        "headline": "",
        "summary": "",
        "experience": [],
        "skills": [],
        "industry": "",
        "target_role": ""
    }


def _map_proxycurl_profile(raw: dict) -> dict:
    """Map Proxycurl response fields to the app's profile schema."""
    profile = _build_empty_profile()

    profile["name"] = raw.get("full_name") or ""
    profile["headline"] = raw.get("occupation") or ""
    profile["summary"] = raw.get("summary") or ""
    profile["industry"] = raw.get("industry") or ""

    skills = raw.get("skills") or []
    if isinstance(skills, list):
        profile["skills"] = [s for s in skills if isinstance(s, str)]

    experiences = raw.get("experiences") or []
    if isinstance(experiences, list):
        mapped_experience = []
        for exp in experiences[:8]:
            if not isinstance(exp, dict):
                continue
            title = exp.get("title") or ""
            company = exp.get("company") or ""
            starts = exp.get("starts_at") or {}
            ends = exp.get("ends_at") or {}
            start_text = ""
            end_text = "Present"
            if isinstance(starts, dict):
                start_text = str(starts.get("year") or "").strip()
            if isinstance(ends, dict) and ends.get("year"):
                end_text = str(ends.get("year"))
            duration = f"{start_text} - {end_text}".strip(" -")
            description = exp.get("description") or ""
            if title or company or description:
                mapped_experience.append({
                    "title": title,
                    "company": company,
                    "duration": duration,
                    "description": description
                })
        profile["experience"] = mapped_experience

    return profile


def _fetch_profile_via_proxycurl(linkedin_url: str):
    """Fetch LinkedIn profile data using Proxycurl API."""
    if not Config.PROXYCURL_API_KEY:
        return None, "PROXYCURL_API_KEY is not configured."

    endpoint = "https://nubela.co/proxycurl/api/v2/linkedin"
    params = {
        "url": linkedin_url,
        "fallback_to_cache": "on-error",
        "use_cache": "if-present",
        "skills": "include"
    }
    headers = {"Authorization": f"Bearer {Config.PROXYCURL_API_KEY}"}

    try:
        response = requests.get(endpoint, params=params, headers=headers, timeout=20)
    except Exception as ex:
        return None, f"Provider request failed: {ex}"

    if response.status_code == 200:
        try:
            payload = response.json()
        except Exception:
            return None, "Provider returned invalid JSON."

        profile = _map_proxycurl_profile(payload)
        if not any([profile["name"], profile["headline"], profile["summary"]]):
            return None, "Provider returned empty profile fields."
        return profile, None

    if response.status_code in (401, 403):
        return None, "Provider API key is invalid or unauthorized."
    if response.status_code == 429:
        return None, "Provider quota exceeded."

    return None, f"Provider returned HTTP {response.status_code}."

# ============================================================
# Frontend Serving Routes
# ============================================================

@app.route("/")
def serve_frontend():
    """Serve the main HTML page."""
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    """Serve static files (CSS, JS, images)."""
    return send_from_directory(FRONTEND_DIR, path)


# ============================================================
# API Routes
# ============================================================

@app.route("/api/analyze", methods=["POST"])
def analyze_profile():
    """
    Analyze a LinkedIn profile and return scored evaluation.
    
    Expects JSON body:
    {
        "name": "John Doe",
        "headline": "Software Engineer at Google",
        "summary": "Experienced engineer...",
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Google",
                "duration": "2020 - Present",
                "description": "Built scalable systems..."
            }
        ],
        "skills": ["Python", "JavaScript", "AWS"],
        "industry": "Technology",
        "target_role": "Senior Software Engineer"
    }
    
    Returns JSON with analysis scores and suggestions.
    """
    ai_check = _require_ai_service()
    if ai_check:
        return ai_check

    # Get profile data from request
    profile_data = request.get_json()
    
    if not profile_data:
        return jsonify({
            "success": False,
            "error": "No profile data provided. Please send JSON body."
        }), 400
    
    # Validate required fields
    validation = analyzer.validate_profile(profile_data)
    if not validation["is_valid"]:
        return jsonify({
            "success": False,
            "error": validation["message"],
            "missing_fields": validation["missing_required"]
        }), 400
    
    # Get quick completeness score (instant, no AI needed)
    completeness = analyzer.quick_completeness_score(profile_data)
    
    # Get AI-powered deep analysis
    ai_analysis = ai_service.analyze_profile(profile_data)
    
    if ai_analysis["success"]:
        # Merge completeness score with AI analysis
        response = {
            "success": True,
            "completeness": completeness,
            "analysis": ai_analysis["analysis"],
            "weak_words_found": {
                "headline": analyzer.find_weak_words(
                    profile_data.get("headline", "")
                ),
                "summary": analyzer.find_weak_words(
                    profile_data.get("summary", "")
                )
            }
        }
    else:
        # AI failed — return completeness score with error
        response = {
            "success": False,
            "completeness": completeness,
            "error": ai_analysis.get("error", "Unknown error"),
            "fallback": True
        }
    
    return jsonify(response)


@app.route("/api/rewrite", methods=["POST"])
def rewrite_section():
    """
    Generate improved versions of a specific profile section.
    
    Expects JSON body:
    {
        "section": "headline",
        "current_content": "Software Engineer at Google",
        "context": {
            "industry": "Technology",
            "target_role": "Senior Software Engineer",
            "experience_years": "5",
            "key_skills": ["Python", "Cloud Architecture", "ML"]
        }
    }
    
    Returns 3 rewritten versions with different styles.
    """
    ai_check = _require_ai_service()
    if ai_check:
        return ai_check

    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "No data provided."
        }), 400
    
    section = data.get("section", "")
    current_content = data.get("current_content", "")
    context = data.get("context", {})
    
    if not section or not current_content:
        return jsonify({
            "success": False,
            "error": "Both 'section' and 'current_content' are required."
        }), 400
    
    # Validate section name
    valid_sections = ["headline", "summary", "experience", "skills"]
    if section.lower() not in valid_sections:
        return jsonify({
            "success": False,
            "error": f"Invalid section. Must be one of: {valid_sections}"
        }), 400
    
    # Get AI rewrites
    result = ai_service.rewrite_section(section, current_content, context)
    return jsonify(result)


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Handle chatbot conversation.
    
    Expects JSON body:
    {
        "message": "How can I improve my headline?",
        "session_id": "optional-session-id",
        "profile_data": { ... optional profile context ... }
    }
    
    Returns AI response maintaining conversation context.
    """
    ai_check = _require_ai_service()
    if ai_check:
        return ai_check

    data = request.get_json()
    
    if not data or not data.get("message"):
        return jsonify({
            "success": False,
            "error": "Message is required."
        }), 400
    
    message = data["message"]
    session_id = data.get("session_id", str(uuid.uuid4()))
    profile_data = data.get("profile_data", None)
    
    # Get AI response
    result = ai_service.chat(session_id, message, profile_data)
    return jsonify(result)


@app.route("/api/chat/clear", methods=["POST"])
def clear_chat():
    """
    Clear a chat conversation history.
    
    Expects JSON body:
    {
        "session_id": "session-id-to-clear"
    }
    """
    data = request.get_json()
    session_id = data.get("session_id", "")
    
    if session_id:
        ai_service.clear_conversation(session_id)
    
    return jsonify({
        "success": True,
        "message": "Conversation cleared."
    })


@app.route("/api/fetch-profile", methods=["POST"])
def fetch_linkedin_profile():
    """Fetch LinkedIn profile from a URL and return parsed fields."""
    data = request.get_json() or {}
    linkedin_url = data.get("linkedin_url", "").strip()
    use_provider = data.get("use_provider", True)

    if Config.LINKEDIN_FETCH_MODE == "manual_only":
        return jsonify({
            "success": False,
            "error": "LinkedIn URL import is disabled in manual mode. Please fill in profile fields manually and click Analyze."
        }), 400

    if not linkedin_url:
        return jsonify({"success": False, "error": "linkedin_url is required."}), 400

    # Normalize URL
    if not linkedin_url.startswith("http"):
        linkedin_url = "https://" + linkedin_url

    provider_error = None
    if use_provider and Config.LINKEDIN_FETCH_MODE == "provider_first":
        if Config.LINKEDIN_PROVIDER == "proxycurl":
            provider_profile, provider_error = _fetch_profile_via_proxycurl(linkedin_url)
            if provider_profile:
                return jsonify({
                    "success": True,
                    "profile": provider_profile,
                    "source": "proxycurl"
                })

    try:
        resp = requests.get(
            linkedin_url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to fetch LinkedIn URL: {e}"}), 400

    # LinkedIn commonly blocks non-browser scraping with HTTP 999.
    if resp.status_code == 999:
        error_msg = (
            "LinkedIn blocked direct server fetch (HTTP 999). "
            "Public profile scraping is restricted. "
            "Configure PROXYCURL_API_KEY in backend/.env to fetch profile data via provider API."
        )
        if provider_error:
            error_msg = f"{error_msg} Provider error: {provider_error}"
        return jsonify({
            "success": False,
            "error": error_msg
        }), 403

    if resp.status_code >= 400:
        return jsonify({
            "success": False,
            "error": f"LinkedIn URL returned HTTP {resp.status_code}."
        }), 400

    soup = BeautifulSoup(resp.text, "html.parser")

    profile = {
        "name": "",
        "headline": "",
        "summary": "",
        "experience": [],
        "skills": [],
        "industry": "",
        "target_role": ""
    }

    # Try JSON-LD data in LinkedIn profile
    for meta_script in soup.find_all("script", type="application/ld+json"):
        if not meta_script.string:
            continue
        try:
            ld_json = json.loads(meta_script.string)
            candidates = ld_json if isinstance(ld_json, list) else [ld_json]
            for item in candidates:
                if not isinstance(item, dict):
                    continue
                if item.get("@type") in {"Person", "ProfilePage"}:
                    profile["name"] = profile["name"] or item.get("name", "")
                    profile["headline"] = profile["headline"] or item.get("headline", "")
                    profile["summary"] = profile["summary"] or item.get("description", "")
        except Exception:
            continue

    # Fallback selectors
    if not profile["name"]:
        if soup.title and soup.title.string:
            profile["name"] = soup.title.string.strip().split("|")[0].strip()
    if not profile["headline"]:
        h2 = soup.find("h2")
        if h2 and h2.get_text().strip():
            profile["headline"] = h2.get_text().strip()

    if not any([profile["name"], profile["headline"], profile["summary"]]):
        error_msg = (
            "Could not extract public profile fields from this URL. "
            "LinkedIn often hides profile data unless accessed through an authenticated browser session."
        )
        if provider_error:
            error_msg = f"{error_msg} Provider error: {provider_error}"
        return jsonify({
            "success": False,
            "error": error_msg
        }), 422

    return jsonify({"success": True, "profile": profile})


@app.route("/api/sample-profile", methods=["GET"])
def get_sample_profile():
    """Return a sample LinkedIn profile for testing."""
    sample = {
        "name": "Alex Johnson",
        "headline": "Software Developer",
        "summary": "I am a software developer with 5 years of experience. I know Python and JavaScript. I have worked on many projects and I am looking for new opportunities. I am a hard worker and team player.",
        "experience": [
            {
                "title": "Software Developer",
                "company": "TechCorp Inc.",
                "duration": "2021 - Present",
                "description": "Responsible for developing web applications. Worked on frontend and backend. Helped the team with various tasks."
            },
            {
                "title": "Junior Developer",
                "company": "StartupXYZ",
                "duration": "2019 - 2021",
                "description": "Worked on the development team. Assisted senior developers with coding tasks. Participated in code reviews."
            }
        ],
        "skills": [
            "Python", "JavaScript", "HTML", "CSS", "Git"
        ],
        "industry": "Technology",
        "target_role": "Senior Software Engineer",
        "education": [
            {
                "degree": "B.S. Computer Science",
                "school": "State University",
                "year": "2019"
            }
        ]
    }
    
    return jsonify(sample)


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "LinkedIn Enhancement Tool API",
        "version": "1.0.0"
    })


# ============================================================
# Error Handlers
# ============================================================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


# ============================================================
# Application Entry Point
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  LinkedIn Enhancement Tool — Backend Server")
    print("=" * 60)
    print(f"  🌐  URL: http://localhost:{Config.PORT}")
    print(f"  📊  API: http://localhost:{Config.PORT}/api/health")
    print(f"  🤖  AI Model: {Config.AI_MODEL}")
    print("=" * 60 + "\n")
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )