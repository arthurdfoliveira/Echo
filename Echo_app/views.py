# Echo/Echo_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
# Imports de formulários removidos

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import DetailView
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.db import IntegrityError 
from django.db.models import Q  # Para consultas complexas
from django.shortcuts import render     

# Importa os modelos da aplicação
from .models import (Noticia, InteracaoNoticia, Notificacao, PerfilUsuario, Categoria)

# Obtém o modelo de usuário configurado no Django
User = get_user_model()


# ===============================================
# Parte de Autenticação e Registro (Raul)
# ===============================================

def registrar(request):
    """
    Renderiza a página de registro e processa a criação de um novo usuário
    usando os campos fornecidos no formulário.
    """
    contexto = {'erros': [], 'dados_preenchidos': {}} 
    
    # Busca todas as categorias para exibir no formulário
    try:
        contexto['todas_categorias'] = Categoria.objects.all()
    except:
        contexto['todas_categorias'] = []
    
    if request.method == "POST":
        # Captura dados enviados pelo formulário
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        categorias_selecionadas_ids = request.POST.getlist('categoria') 

        contexto['dados_preenchidos'] = {
            'username': username,
            'email': email,
            'categorias_selecionadas_ids': categorias_selecionadas_ids, 
        }

        # Validações básicas
        if not username or not email or not password or not password_confirm:
            contexto['erros'].append('Todos os campos obrigatórios devem ser preenchidos: Nome de Usuário, Email e Senha.')
        
        if password != password_confirm:
            contexto['erros'].append('As senhas não coincidem.')
        
        if username and User.objects.filter(username__iexact=username).exists():
            contexto['erros'].append('Este nome de usuário já está em uso. Por favor, escolha outro.')
        
        if email and User.objects.filter(email__iexact=email).exists():
            contexto['erros'].append('Este e-mail já está cadastrado.')

        # Se não houver erros, cria o usuário
        if not contexto['erros']:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Salva as categorias selecionadas no perfil do usuário
                if categorias_selecionadas_ids:
                    categorias = Categoria.objects.filter(pk__in=categorias_selecionadas_ids)
                    perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
                    perfil.categorias_de_interesse.set(categorias)
                
                # Loga o usuário automaticamente
                login(request, user)
                return redirect("Echo_app:dashboard")
                
            except IntegrityError:
                contexto['erros'].append('Erro ao criar usuário. Tente novamente.')
            except Exception as e:
                contexto['erros'].append(f'Ocorreu um erro: {e}')

    # Renderiza a página de registro com os erros/contexto
    return render(request, "Echo_app/registrar.html", contexto)


def entrar(request):
    """
    Renderiza a página de login e processa a autenticação do usuário.
    """
    contexto = {}
    
    if request.method == "POST":
        # Captura dados enviados pelo formulário
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next')  # Para redirecionamento após login

        if not username or not password:
            contexto['erro_login'] = 'Por favor, preencha o usuário e a senha.'
            contexto['username_preenchido'] = username
            return render(request, "Echo_app/entrar.html", contexto)

        # Autentica o usuário
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Login bem-sucedido
            login(request, user)
            if next_url:
                return redirect(next_url)
            else:
                return redirect("Echo_app:dashboard")
        else:
            # Falha na autenticação
            contexto['erro_login'] = 'Usuário ou senha inválidos. Tente novamente.'
            
        contexto['username_preenchido'] = username
            
    return render(request, "Echo_app/entrar.html", contexto)


def sair(request):
    """
    Desloga o usuário e redireciona para a página de login.
    """
    logout(request)
    return redirect("Echo_app:entrar")


# ===============================================
# Parte do Dashboard (Fialho)
# ===============================================

@login_required
def dashboard(request):
    """
    Exibe a página principal do usuário logado,
    com notícias recomendadas, urgentes e categorias de interesse.
    """
    user = request.user
    categorias_interesse = []

    # Obtém o perfil e categorias de interesse
    try:
        perfil = user.perfil 
        categorias_interesse = perfil.categorias_de_interesse.all()
    except PerfilUsuario.DoesNotExist:
        perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
    
    # Notícias recomendadas
    noticias_recomendadas = Noticia.recomendar_para(user)
    
    # Notícias urgentes: 2 mais recentes excluindo recomendadas
    noticias_urgentes = Noticia.objects.exclude(pk__in=noticias_recomendadas.values_list('pk', flat=True)).order_by('-data_publicacao')[:2]

    context = {
        "nome": user.first_name or user.username,
        "email": user.email,
        "noticias_recomendadas": noticias_recomendadas,
        "categorias_interesse": categorias_interesse,
        "noticias_urgentes": noticias_urgentes
    }
    
    return render(request, "Echo_app/dashboard.html", context)


# ===============================================
# Parte de Notícias e Interações (Teteu)
# ===============================================

class NoticiaDetalheView(DetailView):
    """
    Exibe os detalhes de uma única notícia.
    """
    model = Noticia
    template_name = 'Echo_app/noticia_detalhe.html'
    context_object_name = 'noticia'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        noticia = context['noticia']
        
        # Flags para mostrar se o usuário curtiu ou salvou
        context['usuario_curtiu'] = False
        context['usuario_salvou'] = False

        if self.request.user.is_authenticated:
            usuario = self.request.user
            
            context['usuario_curtiu'] = InteracaoNoticia.objects.filter(
                usuario=usuario, noticia=noticia, tipo='CURTIDA'
            ).exists()
            
            context['usuario_salvou'] = InteracaoNoticia.objects.filter(
                usuario=usuario, noticia=noticia, tipo='SALVAMENTO'
            ).exists()

        return context


@require_POST
def toggle_interacao(request, noticia_id, tipo_interacao):
    """
    Adiciona ou remove uma interação (curtida ou salvamento) de uma notícia.
    """
    if tipo_interacao not in ['CURTIDA', 'SALVAMENTO']:
        return HttpResponseBadRequest("Tipo de interação inválido.")

    noticia = get_object_or_404(Noticia, id=noticia_id)
    usuario = request.user
    
    interacao, created = InteracaoNoticia.objects.get_or_create(
        usuario=usuario,
        noticia=noticia,
        tipo=tipo_interacao
    )

    if not created:
        # Se já existia, remove
        interacao.delete()
        acao_realizada = 'removida'
        status_interacao = False
    else:
        acao_realizada = 'adicionada'
        status_interacao = True
    
    # Atualiza contadores
    if tipo_interacao == 'CURTIDA':
        noticia.curtidas_count = noticia.interacoes.filter(tipo='CURTIDA').count()
    elif tipo_interacao == 'SALVAMENTO':
        noticia.salvamentos_count = noticia.interacoes.filter(tipo='SALVAMENTO').count()
    noticia.save()

    # Resposta AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'acao': acao_realizada,
            'nova_contagem': getattr(noticia, f'{tipo_interacao.lower()}s_count'),
            'status_interacao': status_interacao,
            'tipo': tipo_interacao.lower()
        })
    
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def curtir_noticia(request, noticia_id):
    """Atalho para curtir uma notícia"""
    return toggle_interacao(request, noticia_id, 'CURTIDA')


@login_required
@require_POST
def salvar_noticia(request, noticia_id):
    """Atalho para salvar uma notícia"""
    return toggle_interacao(request, noticia_id, 'SALVAMENTO')


# ===============================================
# Parte das Notificações (Oliver)
# ===============================================

@login_required
def lista_notificacoes(request):
    """
    Exibe notificações do usuário, separando recomendadas e outras.
    """
    
    todas_notificacoes = Notificacao.objects.filter(usuario=request.user)
    
    categorias_preferidas = Categoria.objects.none()
    try:
        perfil = request.user.perfil 
        categorias_preferidas = perfil.categorias_de_interesse.all()
    except PerfilUsuario.DoesNotExist:
        pass

    recomendadas = todas_notificacoes.filter(
        noticia__categoria__in=categorias_preferidas
    ).order_by('lida', '-data_criacao')
    
    outras = todas_notificacoes.exclude(
        id__in=recomendadas.values_list('id', flat=True)
    ).order_by('lida', '-data_criacao')
    
    nao_lidas_count = todas_notificacoes.filter(lida=False).count()

    context = {
        'notificacoes_recomendadas': recomendadas,
        'notificacoes_outras': outras,
        'nao_lidas_count': nao_lidas_count
    }

    return render(request, 'Echo_app/notificacao.html', context)


@login_required
@require_POST 
def marcar_notificacao_lida(request, notificacao_id):   
    """
    Marca uma notificação específica como lida.
    """
    notificacao = get_object_or_404(Notificacao, id=notificacao_id, usuario=request.user)
    notificacao.marcar_como_lida()
    return redirect('lista_notificacoes')


@login_required
@require_POST
def marcar_todas_lidas(request):
    """
    Marca todas notificações não lidas como lidas.
    """
    Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)
    return redirect('lista_notificacoes')


# ===============================================
# Parte do Perfil (Raul) com upload de foto
# ===============================================

@login_required
def perfil(request):
    """
    Exibe e permite a atualização do perfil do usuário.
    Atualiza first_name, email, categorias de interesse e foto de perfil.
    """
    usuario = request.user
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=usuario)

    try:
        todas_categorias = Categoria.objects.all()
    except Exception:
        todas_categorias = []

    if request.method == "POST":
        erros = []
        first_name = request.POST.get("first_name", "").strip()
        email = request.POST.get("email", "").strip()
        categorias_ids = request.POST.getlist("categoria")
        foto_perfil = request.FILES.get("foto_perfil")  # captura a foto enviada

        # Validações básicas
        if not email:
            erros.append("Email é obrigatório.")
        elif User.objects.filter(email__iexact=email).exclude(pk=usuario.pk).exists():
            erros.append("Este email já está em uso por outro usuário.")

        if erros:
            context = {
                "usuario": usuario,
                "perfil": perfil,
                "todas_categorias": todas_categorias,
                "erros": erros,
                "dados_preenchidos": {
                    "first_name": first_name,
                    "email": email,
                    "categorias_selecionadas_ids": categorias_ids,
                },
            }
            return render(request, "Echo_app/perfil.html", context)

        # Salva alterações do perfil
        usuario.first_name = first_name
        usuario.email = email
        usuario.save()

        if categorias_ids:
            categorias = Categoria.objects.filter(pk__in=categorias_ids)
            perfil.categorias_de_interesse.set(categorias)
        else:
            perfil.categorias_de_interesse.clear()

        # Salva a foto de perfil se enviada
        if foto_perfil:
            perfil.foto_perfil = foto_perfil
            perfil.save()

        return redirect("Echo_app:perfil")

    # GET
    context = {
        "usuario": usuario,
        "perfil": perfil,
        "todas_categorias": todas_categorias,
    }
    return render(request, "Echo_app/perfil.html", context)


# ===============================================
# Função para criar notícia com imagem (novo)
# ===============================================

@login_required
def criar_noticia(request):
    """
    Permite ao usuário criar uma notícia, incluindo upload de imagem.
    """
    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        conteudo = request.POST.get("conteudo", "").strip()
        categoria_id = request.POST.get("categoria")
        imagem = request.FILES.get("imagem")  # captura imagem enviada

        erros = []
        if not titulo:
            erros.append("O título é obrigatório.")
        if not conteudo:
            erros.append("O conteúdo é obrigatório.")

        categoria = None
        if categoria_id:
            try:
                categoria = Categoria.objects.get(pk=categoria_id)
            except Categoria.DoesNotExist:
                erros.append("Categoria inválida.")

        if erros:
            context = {
                "erros": erros,
                "titulo": titulo,
                "conteudo": conteudo,
                "categorias": Categoria.objects.all(),
                "categoria_selecionada": categoria_id,
            }
            return render(request, "Echo_app/criar_noticia.html", context)

        noticia = Noticia.objects.create(
            titulo=titulo,
            conteudo=conteudo,
            categoria=categoria,
            autor=request.user,
            imagem=imagem
        )

        return redirect("Echo_app:dashboard")

    context = {
        "categorias": Categoria.objects.all()
    }
    return render(request, "Echo_app/criar_noticia.html", context)
