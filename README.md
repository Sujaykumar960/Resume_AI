# ResumeAI — AI-Powered Resume Analyzer & Career Coach

A stunning, production-grade Django 5 web app with user authentication powered by Google Gemini AI.

## Quick Start

### 1. Create & activate virtual environment
```bash
python -m venv 
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux
```
Edit `.env` and add your Gemini API key:
```
GEMINI_API_KEY=your-key-here
```
Get a free key at: https://aistudio.google.com/app/apikey

### 4. Run migrations
```bash
python manage.py migrate
```

### 5. Start the server
```bash
python manage.py runserver
```

Open http://localhost:8000 — done! 🚀

> **No API key?** The app still works with realistic demo data so you can explore the UI immediately.

## Features

### Authentication System
- ✅ Custom user model with email-based authentication
- ✅ User registration with validation
- ✅ Secure login/logout system
- ✅ Protected dashboard and analysis endpoints
- ✅ User-specific analysis history

### Core Features
- 📄 PDF resume upload with drag & drop
- 🤖 Gemini AI analysis (ATS score, job matches, skill gaps)
- 🗺️ 3-year career roadmap
- 💬 AI career coach chatbot with resume context
- 🌙 Stunning dark theme with neon green accents
- 📊 Animated score rings & progress bars
- 🎉 Confetti for high scores (≥85)
- 📜 Personal analysis history
- 📋 One-click copy for improved summary

### Landing Page
- 🎨 Beautiful hero section with floating animations
- ✨ Particle effects and smooth scroll animations
- 📱 Fully responsive design
- 🌟 Feature showcase with hover effects
- 💬 User testimonials section
- 📈 Animated statistics counters
- 🎯 Call-to-action sections

## Project Structure
```
ResumeAI/
├── manage.py
├── resumeai/           # Django project config
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── accounts/           # Authentication app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py      # CustomUser model
│   ├── views.py       # Login, signup, logout
│   ├── forms.py       # Authentication forms
│   ├── urls.py
│   └── templates/
│       └── accounts/
│           ├── login.html
│           └── signup.html
├── core/              # Main resume analysis app
│   ├── models.py      # ResumeAnalysis, ChatMessage
│   ├── views.py       # analyze, results, chat endpoints
│   ├── utils.py       # Gemini helper functions
│   ├── forms.py       # ResumeUploadForm
│   ├── urls.py
│   └── templates/
│       ├── base.html
│       ├── index.html
│       └── results.html
├── templates/         # Global templates
│   ├── home.html      # Landing page
│   └── dashboard.html # Main dashboard
├── media/            # User uploads
├── static/           # Static files
├── requirements.txt
├── .env.example
└── README.md
```

## Tech Stack

- **Backend**: Django 5.x + SQLite (development)
- **Frontend**: Pure vanilla HTML5 + Tailwind CSS + vanilla JavaScript
- **AI**: Google Gemini API (backend only)
- **Database**: SQLite (development), PostgreSQL ready for production
- **Authentication**: Django's built-in auth system with custom user model

## Security Features

- ✅ CSRF protection enabled
- ✅ API keys never exposed to frontend
- ✅ User authentication required for all analysis features
- ✅ Secure file upload handling
- ✅ Environment variable configuration

## Deployment Notes

### Render

1. Push this repository to GitHub and create a new Render Blueprint from the repository. Render will use `render.yaml` to create the web service and PostgreSQL database.
2. In Render, set `SECRET_KEY` to a generated secret, `OPENROUTER_API_KEY` or `GROQ_API_KEY`, and confirm the service's `DATABASE_URL` is connected to PostgreSQL.
3. Render runs migrations and `collectstatic` during the build, then starts Django with Gunicorn.
4. Profile photos and uploaded resumes are stored on the service filesystem. Add a Render persistent disk or object storage before relying on uploads in production.

For a manual Render web service, use:

```text
Build Command: pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
Start Command: gunicorn resumeai.wsgi:application
```

The production settings use `DEBUG=False`, PostgreSQL through `DATABASE_URL`, WhiteNoise for static files, and Render's `RENDER_EXTERNAL_HOSTNAME` automatically.

## API Usage

The app uses Google Gemini 1.5 API for:
- Resume content analysis
- ATS scoring
- Job matching
- Career roadmap generation
- Chat-based coaching

Rate limits may apply based on your Gemini API plan.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.
