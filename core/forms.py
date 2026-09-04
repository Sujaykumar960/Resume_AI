from django import forms


class ResumeUploadForm(forms.Form):
    resume = forms.FileField(
        widget=forms.FileInput(attrs={'accept': '.pdf', 'class': 'hidden'}),
        help_text='PDF only, max 10MB'
    )
    job_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Paste the job description here (optional)…'}),
    )

    def clean_resume(self):
        f = self.cleaned_data['resume']
        if f.content_type != 'application/pdf':
            raise forms.ValidationError('Only PDF files are accepted.')
        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError('File size must be under 10 MB.')
        return f
