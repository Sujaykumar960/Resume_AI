import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from .forms import ResumeUploadForm
from .models import ResumeAnalysis, ChatMessage
from .utils import analyze_resume, chat_with_resume

User = get_user_model()


def home(request):
    """Public landing page"""
    return render(request, 'home.html')


@login_required
def dashboard(request):
    """Main dashboard with resume analyzer - only for authenticated users"""
    user_analyses = ResumeAnalysis.objects.filter(user=request.user).values(
        'id', 
        'filename', 
        'created_at', 
        'analysis_json__overall_score',
        'analysis_json__improvements',
        'analysis_json__job_matches',
        'job_description'
    )[:10]
    return render(request, 'dashboard.html', {
        'form': ResumeUploadForm(), 
        'history': list(user_analyses)
    })


@login_required
@require_POST
def analyze(request):
    form = ResumeUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'error': list(form.errors.values())[0][0]}, status=400)

    pdf = form.cleaned_data['resume']
    job_desc = form.cleaned_data.get('job_description', '')

    try:
        result = analyze_resume(pdf, job_desc)
    except Exception as e:
        msg = str(e)
        if '429' in msg or 'RESOURCE_EXHAUSTED' in msg:
            return JsonResponse({'error': 'Gemini API quota exceeded. Please wait a minute and try again, or check your plan at https://ai.dev/rate-limit'}, status=429)
        return JsonResponse({'error': msg}, status=500)

    analysis = ResumeAnalysis.objects.create(
        user=request.user,
        filename=pdf.name,
        job_description=job_desc,
        analysis_json=result,
    )
    return JsonResponse({'id': str(analysis.id)})


@login_required
def results(request, pk):
    analysis = get_object_or_404(ResumeAnalysis, pk=pk, user=request.user)
    data = analysis.analysis_json
    messages = analysis.messages.values('role', 'content')
    return render(request, 'results.html', {
        'analysis': analysis,
        'data': data,
        'messages_json': json.dumps(list(messages)),
    })


@login_required
@require_POST
def chat(request, pk):
    analysis = get_object_or_404(ResumeAnalysis, pk=pk, user=request.user)
    try:
        body = json.loads(request.body)
        message = body.get('message', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request body.'}, status=400)

    if not message:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)

    history = list(analysis.messages.values('role', 'content'))
    try:
        reply = chat_with_resume(message, analysis.analysis_json, history)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    ChatMessage.objects.create(analysis=analysis, role='user', content=message)
    ChatMessage.objects.create(analysis=analysis, role='model', content=reply)
    return JsonResponse({'reply': reply})


@login_required
def history_list(request):
    items = list(ResumeAnalysis.objects.filter(user=request.user).values(
        'id', 
        'filename', 
        'created_at', 
        'analysis_json__overall_score',
        'analysis_json__improvements',
        'analysis_json__job_matches',
        'job_description'
    ))
    return JsonResponse({'history': items})


@login_required
def mock_interviews(request):
    """AI Mock Interviews page"""
    return render(request, 'mock_interviews.html')


@login_required
def career_opportunities(request):
    """Career Opportunities page"""
    return render(request, 'career_opportunities.html')
