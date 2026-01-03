from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, "store/templates/index.html") 
    #funcion render

def boxes(request):
    pass