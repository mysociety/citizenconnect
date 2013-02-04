from citizenconnect.shortcuts import render

def home(request):
    return render(request, 'index.html')
