# Create your views here.
from citizenconnect.shortcuts import render

def ask_question(request):
    return render(request, 'ask-question.html')

def pick_provider(request):
    return render(request, 'pick-provider.html')

def provider_results(request):
    return render(request, 'provider-results.html')

def question_form(request):
    return render(request, 'question-form.html')

def question_confirm(request):
    return render(request, 'question-confirm.html')
