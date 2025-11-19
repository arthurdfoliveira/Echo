# Echo_app/urls.py (O ARQUIVO DENTRO DO SEU APP)

from django.urls import path
from . import views  # Importa o views.py
from .views import NoticiaDetalheView # Importa a classe específica

app_name = "Echo_app"

urlpatterns = [
    # Autenticação e Perfil
    path("entrar/", views.entrar, name="entrar"),
    path("registrar/", views.registrar, name="registrar"),
    path("sair/", views.sair, name="sair"),
    path("excluir-conta/", views.excluir_conta, name="excluir_conta"),
    path("perfil/", views.perfil_detalhe, name="perfil"),
    path("perfil/editar/", views.perfil_editar, name="perfil_editar"),
    path("perfil/configuracoes/", views.configuracoes_conta, name="configuracoes_conta"),
    
    # ✅ Página Principal
    # Como o arquivo principal já enviou a rota vazia ("") para cá,
    # esta linha faz o 'match' final e carrega o dashboard.
    path("", views.dashboard, name="dashboard"),

    # Notícias (Criação e Interação)
    path("criar-noticia/", views.criar_noticia, name="criar_noticia"),
    path("noticia/<int:pk>/", NoticiaDetalheView.as_view(), name="noticia_detalhe"),
    path("noticia/<int:noticia_id>/curtir/", views.curtir_noticia, name="noticia_curtir"),
    path("noticia/<int:noticia_id>/salvar/", views.salvar_noticia, name="noticia_salvar"),

    # Notificações
    path('notificacoes/', views.lista_notificacoes, name='lista_notificacoes'),
    path('notificacoes/<int:notificacao_id>/marcar_lida/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),
    path('notificacoes/marcar_todas_lidas/', views.marcar_todas_lidas, name='marcar_todas_lidas'),

    # URL da API interna (AJAX para o filtro do dashboard)
    path('filtrar-noticias/', views.filtrar_noticias, name='filtrar_noticias'),
    
    # URL para pesquisa de notícias
    path('pesquisar/', views.pesquisar_noticias, name='pesquisar_noticias'),

    path('curtidas/', views.noticias_curtidas, name='noticias_curtidas'),
    path('salvos/', views.noticias_salvas_view, name='noticias_salvas'),
]