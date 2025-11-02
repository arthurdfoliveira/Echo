# Echo_app/urls.py (O NOVO CÓDIGO CORRIGIDO)

from django.urls import path
from . import views 
from .views import NoticiaDetalheView

urlpatterns = [
    # 1. A raiz (http://127.0.0.1:8000/) agora aponta para o dashboard.
    path("", views.dashboard, name="dashboard"),
    
    # 2. A página de login agora tem a sua própria URL.
    path("entrar/", views.entrar, name="entrar"),
    
    # O resto continua igual
    path("registrar/", views.registrar, name="registrar"),
    path("sair/", views.sair, name="sair"),
    
    path('noticia/<int:pk>/', NoticiaDetalheView.as_view(), name='noticia_detalhe'),
    path('noticia/<int:noticia_id>/curtir/', views.curtir_noticia, name='noticia_curtir'),
    path('noticia/<int:noticia_id>/salvar/', views.salvar_noticia, name='noticia_salvar'),
    path("profile/", views.perfil, name="profile"),     
    
]