# urls.py
from django.urls import path
from .views import RegistroView, LoginView ,TipoEstudianteView

urlpatterns = [
    path('registro/', RegistroView.as_view(), name='registro'),
    path('login/', LoginView.as_view(), name='login'),
    path('tipo-estudiante/', TipoEstudianteView.as_view(), name='tipo-estudiante'),
]


