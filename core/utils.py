import json
import io
import PyPDF2
from django.conf import settings

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

ANALYSIS_SYSTEM_PROMPT = """You are an elite career coach and ATS expert with 15+ years of experience.
Analyze the provided resume and return ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{
  "overall_score": <integer 0-100>,
  "ats_score": <integer 0-100>,
  "content_quality": <integer 0-100>,
  "impact_score": <integer 0-100>,
  "design_score": <integer 0-100>,
  "professional_summary": "<one improved professional summary paragraph ready to copy>",
  "top_jobs": [
    {
      "title": "<job title>",
      "match_percent": <integer>,
      "salary_india": "<e.g. ₹8–15 LPA>",
      "salary_global": "<e.g. $70k–110k USD>"
    }
  ],
  "improvements": [
    {
      "area": "<area name>",
      "before": "<example weak bullet from the actual resume>",
      "after": "<improved version of that bullet>",
      "tip": "<short actionable tip>"
    }
  ],
  "missing_keywords": ["keyword1", "keyword2"],
  "skills_gap": [
    {
      "skill": "<skill name>",
      "importance": "High|Medium|Low",
      "resource": "<free/paid course or project suggestion>"
    }
  ],
  "career_roadmap": [
    {"year": "Year 1", "milestone": "<milestone>", "actions": ["action1", "action2"]},
    {"year": "Year 2", "milestone": "<milestone>", "actions": ["action1", "action2"]},
    {"year": "Year 3", "milestone": "<milestone>", "actions": ["action1", "action2"]}
  ],
  "strengths": ["strength1", "strength2", "strength3"],
  "live_job_opportunities": [
    {
      "company": "<company name>",
      "role": "<job role/title>",
      "location": "<city, state | work mode>",
      "package": "<salary range>",
      "match_percentage": <integer 0-100>,
      "experience": "<experience range>",
      "description": "<2-3 line job description>",
      "key_skills_matched": ["skill1", "skill2", "skill3"]
    }
  ]
}
IMPORTANT: For live_job_opportunities, generate 6-8 realistic, current-feeling job openings based on the candidate's resume. Focus on Indian + global companies that are actively hiring in 2026. Include diverse locations (Mumbai, Bangalore, Hyderabad, Pune, Delhi, Remote) and work modes (Hybrid, Remote, On-site). Make match percentages realistic based on skills alignment. Companies should include tech giants, startups, and established firms.

Base ALL analysis strictly on the actual resume content provided. Return ONLY the JSON. No explanation. No markdown fences."""

CHAT_SYSTEM_PROMPT = """You are ResumeAI Coach — a friendly, expert career advisor.
You have already analyzed the user's resume. Here is the analysis context:
{context}

CRITICAL RULE: You must ONLY answer questions that are directly related to the user's resume, job matching, skills gap, career advice, and future career roadmaps.
If the user asks an off-topic question (such as writing general code unrelated to their career, general knowledge, math, science, recipe instructions, or anything unrelated to their resume and career advice), you must politely decline to answer, stating that you can only assist with resume-related, career, and roadmap questions.

Answer valid questions concisely and helpfully. Use bullet points where appropriate.
Keep responses under 300 words unless a longer answer is clearly needed."""


def _get_client():
    if not OPENAI_AVAILABLE:
        return None
        
    openrouter_key = getattr(settings, 'OPENROUTER_API_KEY', '').strip()
    if openrouter_key:
        return OpenAI(
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/resume-ai-coach",
                "X-Title": "ResumeAI Coach",
            }
        )
        
    groq_key = getattr(settings, 'GROQ_API_KEY', '').strip()
    if groq_key:
        return OpenAI(
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
    return None


def _get_model():
    if getattr(settings, 'OPENROUTER_API_KEY', '').strip():
        return getattr(settings, 'OPENROUTER_MODEL', 'google/gemini-2.5-flash')
    return getattr(settings, 'GROQ_MODEL', 'openai/gpt-oss-120b')


def analyze_resume(pdf_file, job_description=''):
    client = _get_client()
    if not client:
        return _mock_analysis()

    try:
        # Extract text from the PDF file
        pdf_file.seek(0)
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        pdf_text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                pdf_text += page_text + "\n"
        
        # Fallback to mock analysis if extracted text is empty
        if not pdf_text.strip():
            return _mock_analysis()

        prompt = ANALYSIS_SYSTEM_PROMPT
        if job_description:
            prompt += f"\n\nTarget Job Description:\n{job_description}"
        prompt += f"\n\nCandidate Resume Text:\n{pdf_text}"

        model_name = _get_model()
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if Groq/llama adds them anyway
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]

        return json.loads(raw)
    except Exception as e:
        print(f"Error in Groq resume analysis: {e}")
        return _mock_analysis()


def chat_with_resume(message, resume_context, history=None):
    client = _get_client()
    if not client:
        return "API key not configured. Please configure OPENROUTER_API_KEY or GROQ_API_KEY in your .env file."

    try:
        system = CHAT_SYSTEM_PROMPT.format(context=json.dumps(resume_context, indent=2))
        messages = [{"role": "system", "content": system}]
        
        if history:
            for msg in history:
                role = 'assistant' if msg['role'] == 'model' else 'user'
                messages.append({"role": role, "content": msg['content']})
        
        messages.append({"role": "user", "content": message})

        model_name = _get_model()
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.8
        )
        return response.choices[0].message.content
    except Exception as e:
        provider = "OpenRouter" if getattr(settings, 'OPENROUTER_API_KEY', '').strip() else "Groq"
        return f"Error communicating with {provider} API: {str(e)}"


def _mock_analysis():
    """Fallback when API key is not set — returns realistic demo data."""
    return {
        "overall_score": 72,
        "ats_score": 68,
        "content_quality": 75,
        "impact_score": 70,
        "design_score": 80,
        "professional_summary": "Results-driven software engineer with 3+ years of experience building scalable web applications using Python, Django, and React. Proven track record of delivering high-quality solutions that improve user experience and business outcomes.",
        "top_jobs": [
            {"title": "Software Engineer", "match_percent": 88, "salary_india": "₹8–18 LPA", "salary_global": "$80k–130k USD"},
            {"title": "Full Stack Developer", "match_percent": 82, "salary_india": "₹7–16 LPA", "salary_global": "$75k–120k USD"},
            {"title": "Backend Developer", "match_percent": 79, "salary_india": "₹6–14 LPA", "salary_global": "$70k–115k USD"},
            {"title": "Python Developer", "match_percent": 85, "salary_india": "₹7–15 LPA", "salary_global": "$72k–118k USD"},
            {"title": "DevOps Engineer", "match_percent": 60, "salary_india": "₹9–20 LPA", "salary_global": "$90k–140k USD"},
        ],
        "improvements": [
            {"area": "Bullet Points", "before": "Worked on backend APIs", "after": "Designed and deployed 15+ RESTful APIs serving 50k daily requests with 99.9% uptime", "tip": "Quantify every achievement with numbers."},
            {"area": "Action Verbs", "before": "Helped with database optimization", "after": "Optimized PostgreSQL queries reducing average response time by 40%", "tip": "Start every bullet with a strong action verb."},
            {"area": "Skills Section", "before": "Python, Django, SQL", "after": "Python · Django · FastAPI · PostgreSQL · Redis · Docker · AWS EC2", "tip": "List tools with proficiency context."},
        ],
        "missing_keywords": ["CI/CD", "Kubernetes", "Microservices", "System Design", "Agile", "REST API", "Cloud AWS/GCP"],
        "skills_gap": [
            {"skill": "System Design", "importance": "High", "resource": "Grokking the System Design Interview (Educative.io)"},
            {"skill": "Docker & Kubernetes", "importance": "High", "resource": "KodeKloud free Docker course"},
            {"skill": "AWS Cloud", "importance": "Medium", "resource": "AWS Free Tier + A Cloud Guru"},
        ],
        "career_roadmap": [
            {"year": "Year 1", "milestone": "Mid-Level Engineer", "actions": ["Get AWS Certified Developer", "Contribute to 2 open-source projects", "Build a system-design portfolio project"]},
            {"year": "Year 2", "milestone": "Senior Engineer", "actions": ["Lead a team of 3–5 engineers", "Architect a microservices project", "Speak at a local tech meetup"]},
            {"year": "Year 3", "milestone": "Tech Lead / Staff Engineer", "actions": ["Drive cross-team technical decisions", "Mentor junior developers", "Publish technical blog or course"]},
        ],
        "strengths": ["Strong Python fundamentals", "Good project diversity", "Clear educational background"],
        "live_job_opportunities": [
            {
                "company": "Google",
                "role": "Software Engineer - Backend",
                "location": "Bangalore, Karnataka | Hybrid",
                "package": "₹28–42 LPA",
                "match_percentage": 94,
                "experience": "3–6 years",
                "description": "Looking for strong Python + System Design skills to build scalable backend systems for Google Cloud products.",
                "key_skills_matched": ["Python", "Django", "AWS", "System Design"]
            },
            {
                "company": "Microsoft",
                "role": "Full Stack Developer",
                "location": "Hyderabad, Telangana | On-site",
                "package": "₹24–38 LPA",
                "match_percentage": 88,
                "experience": "2–5 years",
                "description": "Join our Azure team to develop cloud-native applications using React, Node.js, and Microsoft Azure services.",
                "key_skills_matched": ["React", "Python", "Cloud", "APIs"]
            },
            {
                "company": "Atlassian",
                "role": "Senior Software Engineer",
                "location": "Mumbai, Maharashtra | Remote",
                "package": "$110k–140k",
                "match_percentage": 85,
                "experience": "4–7 years",
                "description": "Build collaboration tools that help teams work better. Strong focus on distributed systems and microservices.",
                "key_skills_matched": ["Python", "Django", "Microservices", "PostgreSQL"]
            },
            {
                "company": "Swiggy",
                "role": "Backend Engineer - Platform",
                "location": "Bangalore, Karnataka | Hybrid",
                "package": "₹22–35 LPA",
                "match_percentage": 82,
                "experience": "2–4 years",
                "description": "Scale our food delivery platform handling millions of orders daily. Experience with high-traffic systems required.",
                "key_skills_matched": ["Python", "Django", "Redis", "High Performance"]
            },
            {
                "company": "Stripe",
                "role": "Software Engineer - Payments",
                "location": "Pune, Maharashtra | Remote",
                "package": "$120k–150k",
                "match_percentage": 79,
                "experience": "3–5 years",
                "description": "Build global payment infrastructure. Strong focus on security, reliability, and API design at scale.",
                "key_skills_matched": ["Python", "APIs", "Security", "Django"]
            },
            {
                "company": "Zomato",
                "role": "Senior Backend Developer",
                "location": "Delhi, NCR | Hybrid",
                "package": "₹20–32 LPA",
                "match_percentage": 76,
                "experience": "3–6 years",
                "description": "Develop and maintain our food ordering and delivery platform. Work on real-time systems and data analytics.",
                "key_skills_matched": ["Python", "PostgreSQL", "APIs", "Analytics"]
            },
            {
                "company": "Coinbase",
                "role": "Backend Engineer - Crypto",
                "location": "Remote (India) | Remote",
                "package": "$130k–160k",
                "match_percentage": 74,
                "experience": "4–8 years",
                "description": "Build secure, scalable systems for cryptocurrency trading. Focus on blockchain integration and financial systems.",
                "key_skills_matched": ["Python", "Security", "APIs", "System Design"]
            },
            {
                "company": "Ola",
                "role": "Senior Software Engineer - Mobility",
                "location": "Bangalore, Karnataka | On-site",
                "package": "₹18–30 LPA",
                "match_percentage": 71,
                "experience": "2–5 years",
                "description": "Develop ride-hailing platform features including real-time tracking, payment integration, and driver management.",
                "key_skills_matched": ["Python", "Django", "APIs", "Real-time Systems"]
            }
        ]
    }
