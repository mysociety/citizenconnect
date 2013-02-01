from citizenconnect.shortcuts import render

def home(request):
    return render(request, 'index.html')

def askquestion(request):
    return render(request, 'ask-question.html')

