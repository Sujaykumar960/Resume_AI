import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.conf import settings
from google import genai

print("Key prefix:", settings.GEMINI_API_KEY[:12])
client = genai.Client(api_key=settings.GEMINI_API_KEY)

models = list(client.models.list())
print("Total models:", len(models))
for m in models:
    print(m.name)
