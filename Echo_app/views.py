# Echo/Echo_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import DetailView
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm

# Importa os modelos da aplicação
from .models import (Noticia, InteracaoNoticia, Notificacao, PerfilUsuario, Categoria)

# Obtém o modelo de usuário configurado no Django
User = get_user_model()


# ===============================================
# Parte de Autenticação e Registro
# ===============================================

def registrar(request):
    contexto = {'erros': [], 'dados_preenchidos': {}} 
    
    try:
        contexto['todas_categorias'] = Categoria.objects.all()
    except:
        contexto['todas_categorias'] = []
    
    if request.method == "POST":
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

        if not username or not email or not password or not password_confirm:
            contexto['erros'].append('Todos os campos obrigatórios devem ser preenchidos.')
        
        if password != password_confirm:
            contexto['erros'].append('As senhas não coincidem.')
        
        if username and User.objects.filter(username__iexact=username).exists():
            contexto['erros'].append('Este nome de usuário já está em uso.')
        
        if email and User.objects.filter(email__iexact=email).exists():
            contexto['erros'].append('Este e-mail já está cadastrado.')

        if not contexto['erros']:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                
                if categorias_selecionadas_ids:
                    categorias = Categoria.objects.filter(pk__in=categorias_selecionadas_ids)
                    perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
                    perfil.categorias_de_interesse.set(categorias)
                
                login(request, user)
                return redirect("Echo_app:dashboard")
                
            except IntegrityError:
                contexto['erros'].append('Erro ao criar usuário. Tente novamente.')
            except Exception as e:
                contexto['erros'].append(f'Ocorreu um erro: {e}')

    template_name = "Echo_app/registrar.html" if not request.user.is_authenticated else "Echo_app/dashboard.html"
    return render(request, template_name, contexto)


def entrar(request):
    contexto = {}
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next')

        if not username or not password:
            contexto['erro_login'] = 'Por favor, preencha o usuário e a senha.'
            contexto['username_preenchido'] = username
            template_name = "Echo_app/entrar.html" if not request.user.is_authenticated else "Echo_app/dashboard.html"
            return render(request, template_name, contexto)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if next_url:
                return redirect(next_url)
            else:
                return redirect("Echo_app:dashboard")
        else:
            contexto['erro_login'] = 'Usuário ou senha inválidos.'
            
        contexto['username_preenchido'] = username
            
    template_name = "Echo_app/entrar.html" if not request.user.is_authenticated else "Echo_app/dashboard.html"
    return render(request, template_name, contexto)


def sair(request):
    """
    Desloga o usuário e redireciona para o Dashboard (versão offline).
    """
    if request.method == 'POST':
        logout(request)
        messages.success(request, "Você saiu da sua conta com sucesso.")
        # ALTERADO: Redireciona para dashboard em vez de entrar
        return redirect("Echo_app:dashboard") 

    contexto = {
        'titulo': 'Tem certeza que deseja sair?',
        'mensagem': 'Sua sessão será encerrada...',
        'texto_botao': 'Sim, Sair da Conta',
        'url_acao': 'Echo_app:sair', 
        'perigo': False 
    }
    return render(request, "Echo_app/confirmar_acao.html", contexto)


@login_required
def excluir_conta(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        
        try:
            with transaction.atomic():
                user.delete()
                messages.success(request, "Sua conta foi excluída permanentemente.")
        except Exception as e:
            messages.error(request, "Houve um erro ao tentar excluir sua conta.")
            return redirect('Echo_app:entrar')
            
        return redirect('Echo_app:entrar')

    contexto = {
        'titulo': '⚠️ CONFIRMAR EXCLUSÃO DE CONTA ⚠️',
        'mensagem': 'Esta ação é **irreversível**. Todos os seus dados serão removidos.',
        'texto_botao': 'Sim, Excluir Minha Conta Permanentemente',
        'url_acao': 'Echo_app:excluir_conta',
        'perigo': True 
    }
    return render(request, 'Echo_app/confirmar_acao.html', contexto)


# ===============================================
# Parte do Dashboard
# ===============================================

def dashboard(request):
    """
    Exibe a página principal (Logado ou Visitante).
    """
    user = request.user
    categorias_interesse = []
    noticias_recomendadas_list = []

    # 1. Lógica para definir as notícias do Carrossel Principal
    if user.is_authenticated:
        # SE LOGADO: Baseado nas preferências do usuário
        try:
            perfil = user.perfil 
            categorias_interesse = perfil.categorias_de_interesse.all()
        except PerfilUsuario.DoesNotExist:
            perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
        
        noticias_recomendadas_list = Noticia.recomendar_para(user)[:3]
    else:
        # SE VISITANTE: Baseado nas mais curtidas (Maior Engajamento)
        noticias_recomendadas_list = Noticia.objects.order_by('-curtidas_count')[:3]
    
    # 2. Notícias Urgentes
    try:
        urgentes_qs = Noticia.objects.filter(urgente=True).order_by('-data_publicacao')
        if noticias_recomendadas_list:
            # Evita repetir notícias que já estão no carrossel principal
            ids_excluidos = [n.id for n in noticias_recomendadas_list]
            urgentes_qs = urgentes_qs.exclude(id__in=ids_excluidos)
        noticias_urgentes = urgentes_qs[:5] 
    except Exception:
        noticias_urgentes = None

    # 3. Últimas Notícias (Tendências)
    try:
        ultimas_noticias = Noticia.objects.filter(urgente=False).order_by('-data_publicacao')[:5]
    except Exception:
        ultimas_noticias = None
        
    # 4. Categorias para Filtro
    try:
        categorias_para_filtro = Categoria.objects.all()
    except Exception:
        categorias_para_filtro = None

    context = {
        "nome": user.first_name or user.username if user.is_authenticated else "Visitante",
        "email": user.email if user.is_authenticated else "",
        "noticias_recomendadas_list": noticias_recomendadas_list,
        "categorias_interesse": categorias_interesse,
        "noticias_urgentes": noticias_urgentes,
        "ultimas_noticias": ultimas_noticias,
        "categorias_para_filtro": categorias_para_filtro,
        "usuario_autenticado": user.is_authenticated,
    }
    
    # Seleciona o template correto
    template_name = "Echo_app/dashboard.html" if user.is_authenticated else "Echo_app/dashboard_off.html"
    return render(request, template_name, context)


# ===============================================
# VIEW PARA FILTRAR NOTÍCIAS (AJAX)
# ===============================================

def filtrar_noticias(request):
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
    termo_pesquisa = request.GET.get('q', '').strip()
    
    if not termo_pesquisa:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Termo não fornecido'}, status=400)
        return redirect('Echo_app:dashboard')
    
    try:
        noticias_encontradas = Noticia.objects.filter(
            Q(titulo__icontains=termo_pesquisa) | 
            Q(conteudo__icontains=termo_pesquisa)
        ).order_by('-data_publicacao')[:20]
        
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
            
            return JsonResponse({'success': True, 'resultados': resultados, 'total': len(resultados)})
        
        context = {
            'termo_pesquisa': termo_pesquisa,
            'noticias': noticias_encontradas,
            'total_resultados': noticias_encontradas.count()
        }
        return render(request, 'Echo_app/resultados_pesquisa.html', context)
        
    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Erro ao pesquisar'}, status=500)
        return redirect('Echo_app:dashboard')


# ===============================================
# Parte de Notícias e Interações (Detalhes)
# ===============================================

class NoticiaDetalheView(DetailView):
    model = Noticia
    template_name = 'Echo_app/noticia_detalhe.html'
    context_object_name = 'noticia'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        noticia_atual = self.object
        user = self.request.user
        
        qs_base = Noticia.objects.none()

        if user.is_authenticated:
            try:
                perfil = getattr(user, 'perfil', None)
                if perfil and perfil.categorias_de_interesse.exists():
                    qs_base = Noticia.objects.filter(categoria__in=perfil.categorias_de_interesse.all())
            except Exception:
                pass

        if not qs_base.exists():
            qs_base = Noticia.objects.filter(categoria=noticia_atual.categoria)

        noticias_relacionadas = qs_base.exclude(id=noticia_atual.id).order_by('-data_publicacao')[:3]

        if len(noticias_relacionadas) < 3:
            ids_excluidos = [noticia_atual.id] + [n.id for n in noticias_relacionadas]
            quantidade_faltante = 3 - len(noticias_relacionadas)
            mais_recentes = Noticia.objects.exclude(id__in=ids_excluidos).order_by('-data_publicacao')[:quantidade_faltante]
            noticias_relacionadas = list(noticias_relacionadas) + list(mais_recentes)

        context['noticias_relacionadas'] = noticias_relacionadas

        context['usuario_curtiu'] = False
        context['usuario_salvou'] = False

        if self.request.user.is_authenticated:
            context['usuario_curtiu'] = InteracaoNoticia.objects.filter(
                usuario=user, noticia=noticia_atual, tipo='CURTIDA'
            ).exists()
            context['usuario_salvou'] = InteracaoNoticia.objects.filter(
                usuario=user, noticia=noticia_atual, tipo='SALVAMENTO'
            ).exists()

        return context


@require_POST
def toggle_interacao(request, noticia_id, tipo_interacao):
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
        interacao.delete()
        acao_realizada = 'removida'
        status_interacao = False
    else:
        acao_realizada = 'adicionada'
        status_interacao = True
    
    if tipo_interacao == 'CURTIDA':
        noticia.curtidas_count = noticia.interacoes.filter(tipo='CURTIDA').count()
    elif tipo_interacao == 'SALVAMENTO':
        noticia.salvamentos_count = noticia.interacoes.filter(tipo='SALVAMENTO').count()
    noticia.save()

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
    return toggle_interacao(request, noticia_id, 'CURTIDA')


@login_required
@require_POST
def salvar_noticia(request, noticia_id):
    return toggle_interacao(request, noticia_id, 'SALVAMENTO')


# ===============================================
# Parte das Notificações
# ===============================================

@login_required
def lista_notificacoes(request):
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
    notificacao = get_object_or_404(Notificacao, id=notificacao_id, usuario=request.user)
    notificacao.marcar_como_lida()
    return redirect('Echo_app:lista_notificacoes')


@login_required
@require_POST
def marcar_todas_lidas(request):
    Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)
    return redirect('Echo_app:lista_notificacoes')


# ===============================================
# Parte do Perfil
# ===============================================

@login_required
def perfil_detalhe(request):
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=request.user)
    context = {
        'usuario': request.user,
        'perfil': perfil
    }
    return render(request, "Echo_app/perfil.html", context)


@login_required
def perfil_editar(request):
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
        foto_perfil = request.FILES.get("foto_perfil")
        biografia = request.POST.get("biografia", "").strip()

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
                    "biografia": biografia
                },
            }
            return render(request, "Echo_app/perfil_editar.html", context)

        usuario.first_name = first_name
        usuario.email = email
        usuario.save()

        if categorias_ids:
            categorias = Categoria.objects.filter(pk__in=categorias_ids)
            perfil.categorias_de_interesse.set(categorias)
        else:
            perfil.categorias_de_interesse.clear()

        if foto_perfil:
            perfil.foto_perfil = foto_perfil
        
        perfil.biografia = biografia
        perfil.save()

        return redirect("Echo_app:perfil")

    context = {
        "usuario": usuario,
        "perfil": perfil,
        "todas_categorias": todas_categorias,
    }
    return render(request, "Echo_app/perfil_editar.html", context)


# ===============================================
# Função para criar notícia
# ===============================================

@login_required
def criar_noticia(request):
    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        conteudo = request.POST.get("conteudo", "").strip()
        categoria_id = request.POST.get("categoria")
        imagem = request.FILES.get("imagem")

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

        Noticia.objects.create(
            titulo=titulo,
            conteudo=conteudo,
            categoria=categoria,
            autor=request.user,
            imagem=imagem,
            urgente=request.POST.get('urgente') == 'on'
        )

        return redirect("Echo_app:dashboard")

    context = {
        "categorias": Categoria.objects.all()
    }
    return render(request, "Echo_app/criar_noticia.html", context)


# ===============================================
# Configurações da conta
# ===============================================

@login_required
def configuracoes_conta(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) 
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('Echo_app:configuracoes_conta')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'form': form
    }
    return render(request, 'Echo_app/configuracoes.html', context)


# ===============================================
# LISTA DE NOTÍCIAS CURTIDAS
# ===============================================

# ===============================================
# LISTA DE NOTÍCIAS CURTIDAS (CORRIGIDA)
# ===============================================

@login_required
def noticias_curtidas(request):
    usuario = request.user
    
    # Parâmetros de Filtro/Pesquisa da URL
    termo_pesquisa = request.GET.get('q', '').strip()
    categoria_slug = request.GET.get('categoria', '').strip()
    
    # 1. Busca todas as interações de 'CURTIDA' do usuário
    interacoes_qs = InteracaoNoticia.objects.filter(
        usuario=usuario, 
        tipo='CURTIDA'
    ).select_related('noticia', 'noticia__categoria').order_by('-data_interacao')
    
    # 2. Aplica filtro de Categoria, se houver
    if categoria_slug:
        # Filtra interações que pertencem a notícias da categoria selecionada (usando o slug)
        # Se o seu slug estiver em branco no banco, isso pode falhar.
        interacoes_qs = interacoes_qs.filter(noticia__categoria__slug=categoria_slug)
        
    # 3. Aplica filtro de Pesquisa, se houver
    if termo_pesquisa:
        # Filtra interações onde o título ou conteúdo da notícia contenha o termo
        interacoes_qs = interacoes_qs.filter(
            Q(noticia__titulo__icontains=termo_pesquisa) | 
            Q(noticia__conteudo__icontains=termo_pesquisa)
        )
        
    # 4. Extrai as notícias, garantindo unicidade e mantendo a ordem.
    # Usamos list comprehension para extrair a notícia de cada interação no queryset filtrado.
    noticias_curtidas_com_duplicatas = [item.noticia for item in interacoes_qs]
    
    # Remove duplicatas mantendo a ordem (necessário se o mesmo usuário puder curtir a notícia
    # múltiplas vezes, o que o modelo InteracaoNoticia permite).
    seen_ids = set()
    noticias_curtidas = []
    for noticia in noticias_curtidas_com_duplicatas:
        if noticia.id not in seen_ids:
            noticias_curtidas.append(noticia)
            seen_ids.add(noticia.id)

    # 5. Carrega TODAS as categorias para o filtro do template
    categorias_disponiveis = Categoria.objects.all().order_by('nome')

    context = {
        'noticias_curtidas': noticias_curtidas,
        'categorias_disponiveis': categorias_disponiveis, 
        'total_curtidas': len(noticias_curtidas),
        # Passa o slug ativo para o HTML para manter o estado do botão
        'categoria_ativa': categoria_slug 
    }
    
    return render(request, 'Echo_app/noticias_curtidas.html', context)

# ===============================================
# LISTA DE NOTÍCIAS SALVAS
# ===============================================

@login_required
def noticias_salvas_view(request):
    usuario = request.user

    interacoes = InteracaoNoticia.objects.filter(
        usuario=usuario, 
        tipo='SALVAMENTO'
    ).select_related('noticia', 'noticia__categoria').order_by('-data_interacao')

    seen_ids = set()
    noticias = []
    for item in interacoes:
        if item.noticia.id not in seen_ids:
            noticias.append(item.noticia)
            seen_ids.add(item.noticia.id)
    
    categorias = Categoria.objects.all()

    context = {
        'noticias_salvas': noticias,
        'categorias': categorias,
        'total_salvos': len(noticias)
    }
    return render(request, 'Echo_app/noticias_salvas.html', context)