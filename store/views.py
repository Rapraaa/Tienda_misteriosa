from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, "store/templates/home.html") 
    #funcion render


def boxes(request):
    pass