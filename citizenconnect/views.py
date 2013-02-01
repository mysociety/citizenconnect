from citizenconnect.shortcuts import render

def home(request):
    return render(request, 'index.html')

def ask_question(request):
    return render(request, 'ask-question.html')

def pick_provider(request):
    return render(request, 'pick-provider.html')

