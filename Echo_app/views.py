# Echo/Echo_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
# Imports de formulários removidos
from django.contrib import messages     
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import DetailView
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.db import IntegrityError 
from django.db.models import Q  # Para consultas complexas
from django.shortcuts import render  
from django.db import transaction   
from django.contrib.auth.models import User
from .models import PerfilUsuario, Categoria

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
    Desloga o usuário (POST) e redireciona para a tela de login.
    """
    if request.method == 'POST':
        # 1. Executa o logout
        logout(request)
        
        # 2. Adiciona a mensagem (opcional, pode ser ignorada após logout)
        messages.success(request, "Você saiu da sua conta com sucesso.")
            
        # 3. REDIRECIONA DEFINITIVAMENTE para a tela de LOGIN
        return redirect("Echo_app:entrar") 


    # Se for GET (página de confirmação)
    contexto = {
        # ... (contexto que usa confirmar_acao.html)
        'titulo': 'Tem certeza que deseja sair?',
        'mensagem': 'Sua sessão será encerrada...',
        'texto_botao': 'Sim, Sair da Conta',
        'url_acao': 'Echo_app:sair', 
        'perigo': False 
    }
    return render(request, "Echo_app/confirmar_acao.html", contexto)

login_required
def excluir_conta(request):
    """
    Exibe a confirmação de exclusão (GET) ou exclui a conta (POST).
    Usa o template dinâmico 'confirmar_acao.html'.
    """
    if request.method == 'POST':
        user = request.user
        # Se for POST, realiza a ação destrutiva
        logout(request)
        
        try:
            with transaction.atomic():
                user.delete()
                messages.success(request, "Sua conta foi excluída permanentemente. Lamentamos te ver partir.")
        except Exception as e:
            messages.error(request, "Houve um erro ao tentar excluir sua conta.")
            return redirect('Echo_app:entrar')
            
        return redirect('Echo_app:entrar')

    # ESTE BLOCO (GET) ESTAVA FALTANDO OU INCOMPLETO
    # Aqui, definimos o contexto para a tela de confirmação
    contexto = {
        'titulo': '⚠️ CONFIRMAR EXCLUSÃO DE CONTA ⚠️',
        'mensagem': 'Esta ação é **irreversível**. Todos os seus dados, preferências e histórico serão permanentemente removidos.',
        'texto_botao': 'Sim, Excluir Minha Conta Permanentemente',
        'url_acao': 'Echo_app:excluir_conta', # URL para onde o formulário POST deve ir
        'perigo': True 
    }
    # Fim da correção. Agora o render tem o contexto.
    return render(request, 'Echo_app/confirmar_acao.html', contexto)

# ===============================================
# Parte do Dashboard (ATUALIZADA)
# ===============================================


def dashboard(request):
    """
    Exibe a página principal do usuário logado ou visitante,
    com notícias recomendadas, urgentes e as últimas notícias gerais.
    """
    user = request.user
    categorias_interesse = []
    noticias_recomendadas = None

    # Verifica se o usuário está autenticado
    if user.is_authenticated:
        # Obtém o perfil e categorias de interesse
        try:
            perfil = user.perfil 
            categorias_interesse = perfil.categorias_de_interesse.all()
        except PerfilUsuario.DoesNotExist:
            perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
        
        # Notícias recomendadas (Pega a primeira recomendada)
        noticias_recomendadas = Noticia.recomendar_para(user).first()
    
    # Notícias urgentes: 5 mais recentes
    try:
        urgentes_qs = Noticia.objects.filter(urgente=True).order_by('-data_publicacao')
        if noticias_recomendadas:
            urgentes_qs = urgentes_qs.exclude(pk=noticias_recomendadas.pk)
        noticias_urgentes = urgentes_qs[:5] 
    except Exception:
        noticias_urgentes = None

    # Últimas notícias: 5 mais recentes (para a aba "Tendências"), EXCLUINDO urgentes
    try:
        ultimas_noticias = Noticia.objects.filter(urgente=False).order_by('-data_publicacao')[:5]
    except Exception:
        ultimas_noticias = None
        
    # Busca TODAS as categorias para os botões de filtro
    try:
        categorias_para_filtro = Categoria.objects.all()
    except Exception:
        categorias_para_filtro = None

    context = {
        "nome": user.first_name or user.username if user.is_authenticated else "Visitante",
        "email": user.email if user.is_authenticated else "",
        "noticia_recomendada": noticias_recomendadas, 
        "categorias_interesse": categorias_interesse,
        "noticias_urgentes": noticias_urgentes,
        "ultimas_noticias": ultimas_noticias,
        "categorias_para_filtro": categorias_para_filtro,
        "usuario_autenticado": user.is_authenticated,  # Flag para o template
    }
    
    return render(request, "Echo_app/dashboard.html", context)


# ===============================================
# NOVA VIEW PARA FILTRAR NOTÍCIAS (AJAX)
# ===============================================

def filtrar_noticias(request):
    """
    Esta view é chamada pelo JavaScript (Fetch) do dashboard.
    Ela filtra as notícias com base na categoria pedida
    e retorna APENAS o HTML da lista de notícias.
    Não requer login.
    """
    categoria_nome = request.GET.get('categoria')
    
    if not categoria_nome:
        return HttpResponseBadRequest("Categoria não fornecida.")

    try:
        if categoria_nome == 'Tendências':
            noticias_filtradas = Noticia.objects.filter(urgente=False).order_by('-data_publicacao')[:5]
        else:
            noticias_filtradas = Noticia.objects.filter(
                categoria__nome__iexact=categoria_nome,
                urgente=False 
            ).order_by('-data_publicacao')[:5]
            
    except Exception as e:
        print(f"Erro ao filtrar notícias: {e}") 
        noticias_filtradas = None

    context = {
        'ultimas_noticias': noticias_filtradas
    }
    
    return render(request, 'Echo_app/partials/lista_noticias.html', context)


# ===============================================
# VIEW PARA PESQUISAR NOTÍCIAS
# ===============================================

def pesquisar_noticias(request):
    """
    Busca notícias por título ou conteúdo com base no termo de pesquisa.
    Retorna os resultados em formato HTML ou JSON.
    """
    termo_pesquisa = request.GET.get('q', '').strip()
    
    if not termo_pesquisa:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Termo de pesquisa não fornecido'
            }, status=400)
        return redirect('Echo_app:dashboard')
    
    # Busca notícias que contenham o termo no título ou conteúdo
    try:
        noticias_encontradas = Noticia.objects.filter(
            Q(titulo__icontains=termo_pesquisa) | 
            Q(conteudo__icontains=termo_pesquisa)
        ).order_by('-data_publicacao')[:20]
        
        # Se for requisição AJAX, retorna JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            resultados = []
            for noticia in noticias_encontradas:
                resultados.append({
                    'id': noticia.id,
                    'titulo': noticia.titulo,
                    'conteudo': noticia.conteudo[:150] + '...' if len(noticia.conteudo) > 150 else noticia.conteudo,
                    'categoria': noticia.categoria.nome if noticia.categoria else 'Geral',
                    'data_publicacao': noticia.data_publicacao.strftime('%d/%m/%Y'),
                    'imagem_url': noticia.imagem.url if noticia.imagem else None,
                    'url': f"/noticia/{noticia.id}/"
                })
            
            return JsonResponse({
                'success': True,
                'resultados': resultados,
                'total': len(resultados)
            })
        
        # Se não for AJAX, renderiza uma página de resultados
        context = {
            'termo_pesquisa': termo_pesquisa,
            'noticias': noticias_encontradas,
            'total_resultados': noticias_encontradas.count()
        }
        return render(request, 'Echo_app/resultados_pesquisa.html', context)
        
    except Exception as e:
        print(f"Erro ao pesquisar notícias: {e}")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Erro ao realizar a pesquisa'
            }, status=500)
        return redirect('Echo_app:dashboard')

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
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Usuário não autenticado'}, status=401)
        
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
    return redirect('Echo_app:lista_notificacoes')


@login_required
@require_POST
def marcar_todas_lidas(request):
    """
    Marca todas notificações não lidas como lidas.
    """
    Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)
    return redirect('Echo_app:lista_notificacoes')


# ===============================================
# Parte do Perfil (Raul) com upload de foto
# ===============================================

@login_required
def perfil_detalhe(request):
    """
    Apenas EXIBE a página de perfil bonita (o seu perfil.html).
    """
    # Esta view é simples, só precisa renderizar o template.
    # O seu template 'perfil.html' já pega 'request.user.email'
    return render(request, "Echo_app/perfil.html")

@login_required
def perfil_editar(request):
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
            return render(request, "Echo_app/perfil_editar.html", context)

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
    return render(request, "Echo_app/perfil_editar.html", context)


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
            imagem=imagem,
            urgente=request.POST.get('urgente') == 'on' # Captura o status de urgente
        )

        return redirect("Echo_app:dashboard")

    context = {
        "categorias": Categoria.objects.all()
    }
    return render(request, "Echo_app/criar_noticia.html", context)