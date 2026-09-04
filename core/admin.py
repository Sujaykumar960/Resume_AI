from django.contrib import admin
from .models import ResumeAnalysis, ChatMessage

@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = ('filename', 'created_at')
    readonly_fields = ('id', 'analysis_json', 'created_at')

admin.site.register(ChatMessage)
