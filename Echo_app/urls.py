# Echo_app/urls.py (O NOVO CÓDIGO CORRIGIDO)

from django.urls import path
from . import views 
from .views import NoticiaDetalheView
from . import views
from Echo_app import views as app_views

app_name = "Echo_app"


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("entrar/", views.entrar, name="entrar"),
    path("registrar/", views.registrar, name="registrar"),
    path("sair/", views.sair, name="sair"),
    path("noticia/<int:pk>/", NoticiaDetalheView.as_view(), name="noticia_detalhe"),
    path("noticia/<int:noticia_id>/curtir/", views.curtir_noticia, name="noticia_curtir"),
    path("noticia/<int:noticia_id>/salvar/", views.salvar_noticia, name="noticia_salvar"),
    path("perfil/", views.perfil, name="perfil"),
    path('notificacoes/', app_views.lista_notificacoes, name='lista_notificacoes'),
]
