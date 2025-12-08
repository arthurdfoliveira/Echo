from django.urls import path
from . import views

app_name = 'Echo_app'

urlpatterns = [
    # --- Rotas Principais ---
    path('', views.dashboard, name='dashboard'),
    path('registrar/', views.registrar, name='registrar'),
    path('entrar/', views.entrar, name='entrar'),
    path('sair/', views.sair, name='sair'),
    path('excluir-conta/', views.excluir_conta, name='excluir_conta'),
    
    # --- Configurações e Perfil ---
    path('configuracoes/', views.configuracoes_conta, name='configuracoes_conta'),
    path('perfil/', views.perfil_detalhe, name='perfil'),
    path('perfil/editar/', views.perfil_editar, name='perfil_editar'),

    # --- Notícias ---
    path('criar-noticia/', views.criar_noticia, name='criar_noticia'),
    path('noticia/<int:pk>/', views.NoticiaDetalheView.as_view(), name='noticia_detalhe'),
    path('filtrar-noticias/', views.filtrar_noticias, name='filtrar_noticias'),
    path('pesquisar/', views.pesquisar_noticias, name='pesquisar_noticias'),
    
    # --- Interações (Curtir/Salvar) ---
    path('noticia/<int:noticia_id>/curtir/', views.curtir_noticia, name='curtir_noticia'),
    path('noticia/<int:noticia_id>/salvar/', views.salvar_noticia, name='salvar_noticia'),
    path('curtidas/', views.noticias_curtidas, name='noticias_curtidas'),
    path('salvos/', views.noticias_salvas_view, name='noticias_salvas'),

    # --- Notificações ---
    path('notificacoes/', views.lista_notificacoes, name='lista_notificacoes'),
    path('notificacoes/ler/<int:notificacao_id>/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),
    path('notificacoes/ler-todas/', views.marcar_todas_lidas, name='marcar_todas_lidas'),

    # 🔑 --- RECUPERAÇÃO DE SENHA (AGORA COMPLETO) --- 🔑
    path('esqueci-senha/', views.iniciar_redefinicao_otp, name='esqueci_senha'),
    path('verificar-otp/', views.verificar_codigo, name='verificar_codigo'),
    path('redefinir-senha/', views.redefinir_senha_final, name='redefinir_senha_final'),
    path('reenviar-codigo/', views.reenviar_codigo, name='reenviar_codigo'),
    path('senha-concluida/', views.senha_concluida, name='senha_concluida'), # Adição da nova URL

    # --- Jogos ---
    path('games/jogo-da-velha/', views.jogo_da_velha_view, name='jogo_da_velha'),
    path('games/memoria/', views.jogo_da_memoria, name='jogo_da_memoria'),
    path('games/forca/', views.jogo_da_forca, name='jogo_da_forca'), # O caminho necessário
    path('games/', views.games, name='games'),
]