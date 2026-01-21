from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'), #el next page le dices a donde
    #EL LOGOUT SOLO TRABAJA CON POST, NO CON GET
  #cambio de contraSE;A
    path('password/change', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password/change/done', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'), 
    #registro
    path('registro/', registro, name='registro'),

]
