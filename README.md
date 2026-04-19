# LinkedIn Enhancer

**AI-Powered LinkedIn Profile & Content Analysis Tool**

Transform your LinkedIn presence with intelligent AI-driven insights and suggestions. Get personalized recommendations for profile optimization, content improvement, and professional engagement strategies.

**Live Demo:** https://linkedin-enhancer.onrender.com

---

## 🎯 Features

### Profile Analysis
- **Completeness Scoring** - Assess your profile readiness (0-100%)
- **Headline Quality Analysis** - Get specific improvement suggestions
- **Weakness Detection** - Identify generic phrases and weak language
- **AI-Powered Insights** - Domain-expert recommendations using Gemini API

### Content Enhancement
- **Section Rewriting** - Generate 3 professional variants for any profile section
- **Comment Suggestions** - Create 4 distinct comment styles (professional, engaging, witty, supportive)
- **Content Tone Analysis** - Analyze posts for tone, intent, and engagement potential
- **Post Summarization** - Condense LinkedIn posts into concise 2-sentence summaries

### Interactive Chatbot
- **Conversation Memory** - Multi-turn conversations with context awareness
- **Context-Aware Responses** - AI understands your profile, posts, and history
- **Strategic Advice** - Get personalized LinkedIn career coaching
- **Real-Time Suggestions** - Instant feedback on any LinkedIn-related question

### Browser Integration
- **Chrome Extension** - Native LinkedIn.com integration via side panel
- **One-Click Analysis** - Profile insights directly from LinkedIn pages
- **Seamless Experience** - No need to leave LinkedIn platform

---

## 🚀 Quick Start

### Web Application

**Access Instantly:**
```
https://linkedin-enhancer.onrender.com
```

**No installation required!** Just:
1. Visit the URL above
2. Enter your LinkedIn profile data
3. Get instant AI-powered analysis

### Chrome Extension

**Installation Steps:**
1. Clone the repository:
   ```bash
   git clone https://github.com/ig-hraj/linkedIn-enhancer.git
   cd linkedIn-enhancer
   ```

2. Navigate to `chrome://extensions` in your browser

3. Enable **Developer mode** (toggle in top right)

4. Click **Load unpacked**

5. Select the `extension/` folder

6. Go to any LinkedIn page and click the extension icon!

**For detailed setup:** See [EXTENSION_SETUP.md](../EXTENSION_SETUP.md)

---

## 💻 Technology Stack

### Frontend
- **HTML5, CSS3, Vanilla JavaScript (ES6+)**
- Responsive design
- No build tools required

### Backend
- **Python 3.8+** with Flask 3.1.1
- **Gunicorn 22.0.0** (production WSGI server)
- **Flask-CORS 5.0.1** (cross-origin support)

### AI/ML
- **Google Gemini API** (google-generativeai 0.8.5)
- **Model:** gemini-flash-lite-latest (with fallback chain)
- **Temperature:** 0.7 (balanced creativity)
- **Top-p:** 0.9 (diverse outputs)

### Data & Storage
- **Session Memory:** In-process dictionary
- **Environment Config:** python-dotenv 1.1.0
- **HTTP Client:** requests 2.31.0
- **HTML Parser:** beautifulsoup4 4.12.2

### Deployment
- **Cloud Platform:** Render.com (free tier)
- **Version Control:** Git + GitHub
- **HTTPS:** Automatic SSL certificates

---

## 📋 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/analyze` | POST | Profile analysis & scoring |
| `/api/rewrite` | POST | Section rewriting (3 variants) |
| `/api/chat` | POST | Standard chatbot |
| `/api/ext-chat` | POST | Extension context-aware chat |
| `/api/chat/clear` | POST | Clear conversation history |
| `/api/analyze-content` | POST | Content tone & intent analysis |
| `/api/suggest-comments` | POST | Generate 4 comment styles |
| `/api/quick-comment` | POST | Quick response generation |
| `/api/auto-extract-analyze` | POST | Auto-extract & analyze |
| `/api/health` | GET | Server health check |
| `/api/sample-profile` | GET | Sample test profile |
| `/` | GET | Serve web application |

---

## 🔧 Configuration

### Environment Variables

Create a `backend/.env` file:

```env
# Google Gemini API Configuration
GEMINI_API_KEY=your_api_key_here
AI_MODEL=gemini-flash-lite-latest

# LinkedIn Fetch Mode
LINKEDIN_FETCH_MODE=manual_only

# Model Parameters
TEMPERATURE=0.7
MAX_TOKENS=1500

# Server Configuration
DEBUG=False
HOST=0.0.0.0
PORT=5000
```

### Getting API Key

1. Visit: https://console.cloud.google.com/
2. Create a new project
3. Enable Generative AI API
4. Create API key credentials
5. Paste key in `.env` file

**Never commit `.env` to Git!** It's in `.gitignore` for security.

---

## 📦 Installation (Local Development)

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git

### Setup Steps

1. **Clone repository:**
   ```bash
   git clone https://github.com/ig-hraj/linkedIn-enhancer.git
   cd linkedIn-enhancer/backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   .\.venv\Scripts\Activate.ps1
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API key
   ```

5. **Run locally:**
   ```bash
   python app.py
   ```

6. **Access application:**
   ```
   http://localhost:5000
   ```

---

## 🌐 Production Deployment

### Deploy to Render

1. **Push to GitHub** (repository must be public):
   ```bash
   git push origin main
   ```

2. **Connect to Render:**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Select repository: `linkedIn-enhancer`

3. **Configure:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Environment Variables:** Add your `GEMINI_API_KEY`

4. **Deploy:**
   - Click "Create Web Service"
   - Render builds and deploys automatically
   - Access at: `https://your-service.onrender.com`

### Verify Deployment

```bash
# Check health endpoint
curl https://your-service.onrender.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "service": "LinkedIn Enhancement Tool API",
  "features": ["analyze", "rewrite", "chat", ...]
}
```

---

## 🧪 Testing

### API Testing with cURL

```bash
# Profile Analysis
curl -X POST https://linkedin-enhancer.onrender.com/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "headline": "Software Engineer",
    "experience": ["Senior Engineer 3yr", "Engineer 2yr"],
    "skills": ["Python", "React", "AWS"]
  }'

# Chatbot
curl -X POST https://linkedin-enhancer.onrender.com/api/ext-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How can I improve my headline?",
    "context": "profile",
    "session_id": "demo_123"
  }'

# Health Check
curl https://linkedin-enhancer.onrender.com/api/health
```

### Testing Extension

1. Load unpacked extension in Chrome
2. Go to any LinkedIn page
3. Click extension icon
4. Test features:
   - Profile analysis
   - Comment suggestions
   - Chatbot

---

## 📊 Project Structure

```
linkedin-enhancer/
├── backend/                          # Flask API Server
│   ├── app.py                       # Main server (13 endpoints)
│   ├── ai_service.py                # Gemini API integration
│   ├── config.py                    # Configuration management
│   ├── profile_analyzer.py          # Profile validation & scoring
│   ├── prompts.py                   # LLM prompt templates
│   ├── requirements.txt             # Python dependencies
│   ├── render.yaml                  # Render deployment config
│   ├── Procfile                     # Process definition
│   ├── .env                         # Local secrets (not committed)
│   ├── .env.example                 # Secrets template
│   ├── .gitignore                   # Git exclusions
│   └── frontend/                    # Web UI
│       ├── index.html
│       ├── css/styles.css
│       └── js/app.js, analysis.js, chat.js
│
├── extension/                        # Chrome Extension
│   ├── manifest.json                # Extension config
│   ├── background/service-worker.js # Message router
│   ├── sidepanel/panel.html/js/css  # Side panel UI
│   ├── content/content.js           # LinkedIn page injection
│   ├── content/extractor.js         # Data extraction
│   └── icons/                       # Extension icons
│
├── sample-data/
│   └── sample_profiles.json         # Test profiles
│
├── README.md                        # This file
├── EXTENSION_SETUP.md               # Extension installation guide
└── PROJECT_SUBMISSION_MANUAL.md     # Full project documentation
```

---

## 🔐 Security

### Best Practices Implemented

- ✅ **Secrets Protection:** API keys never committed (`.gitignore`)
- ✅ **Environment Variables:** Sensitive config via `.env`
- ✅ **Input Validation:** All endpoints validate user input
- ✅ **CORS Configuration:** Restricted to safe origins
- ✅ **HTTPS Enforcement:** Production uses SSL/TLS
- ✅ **Error Handling:** Sanitized error messages
- ✅ **Session Safety:** Opaque session IDs (not predictable)

### API Key Security

1. **Never hardcode** API keys in source
2. **Use environment variables** for all secrets
3. **Rotate keys** if accidentally exposed
4. **Restrict permissions** to minimum required
5. **Monitor usage** via API provider dashboard

---

## 🎓 Learning Outcomes

This project demonstrates:

- **Generative AI Integration** - Practical Gemini API usage
- **Prompt Engineering** - Domain-specific prompt design
- **Full-Stack Development** - Frontend, backend, extension
- **API Design** - RESTful architecture with 13+ endpoints
- **Production Deployment** - Cloud deployment on Render
- **Security Best Practices** - Secrets management, validation
- **Session Management** - Conversation memory implementation
- **Model Configuration** - Temperature, Top-p parameter tuning

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📝 License

This project is open source and available under the MIT License.

---

## 🙋 Support

### Getting Help

- **API Issues:** Check `/api/health` endpoint
- **Extension Issues:** See [EXTENSION_SETUP.md](../EXTENSION_SETUP.md)
- **Project Details:** Read [PROJECT_SUBMISSION_MANUAL.md](../PROJECT_SUBMISSION_MANUAL.md)
- **Code:** See inline comments in source files

### Common Issues

**Q: "Backend is running" error appears**
- A: Hard refresh browser (Ctrl+Shift+Delete), clear cache

**Q: Extension not showing on LinkedIn**
- A: Ensure extension is enabled in `chrome://extensions`
- A: Verify you're on `linkedin.com` domain

**Q: API rate limit exceeded**
- A: Using free Gemini tier - wait before next request
- A: Consider upgrading to paid API plan for higher limits

**Q: Environment variable not loading**
- A: Ensure `.env` file is in `backend/` folder
- A: Restart server after editing `.env`

---

## 📞 Contact

**Project:** LinkedIn Enhancer  
**Course:** INT428 - Project-Based Assessment  
**Domain:** Generative AI Chatbot Using APIs  

---

## 🎉 Acknowledgments

- **Google Gemini API** - AI backbone
- **Flask** - Web framework
- **Render** - Cloud hosting
- **Chrome Web Store** - Extension platform

---

**Last Updated:** April 19, 2026  
**Version:** 2.1.0  
**Status:** Production Deployment Active ✅

---

**Ready to optimize your LinkedIn presence?**  
Visit: https://linkedin-enhancer.onrender.com 🚀
