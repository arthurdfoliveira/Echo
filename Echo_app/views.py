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
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from django.core.paginator import Paginator

# --- IMPORTS PARA AVATARES E RECUPERAÇÃO DE SENHA ---
import os
import random  # Para gerar o código OTP
from django.conf import settings
from django.core.files import File
from django.core.mail import send_mail 
from django.template.loader import render_to_string # NOVO: Para renderizar o template de email
from django.utils.html import strip_tags # NOVO: Para criar a versão texto do email
# ----------------------------------------------------

from .models import (Noticia, InteracaoNoticia, Notificacao, PerfilUsuario, Categoria)

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
    if request.method == 'POST':
        logout(request)
        messages.success(request, "Você saiu da sua conta com sucesso.")
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
# LÓGICA DE RECUPERAÇÃO DE SENHA (OTP) - CORRIGIDA
# ===============================================

def iniciar_redefinicao_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            
            # Gera um código de 6 dígitos
            otp = random.randint(100000, 999999)
            
            # Salva na sessão: ID do usuário e o código OTP
            request.session['reset_user_id'] = user.pk
            request.session['otp_code'] = str(otp) 
            
            # --- DEBUG: Mostra o código no terminal ---
            print(f"\n[DEBUG] CÓDIGO DE RECUPERAÇÃO PARA {email}: {otp}\n")
            # ------------------------------------------
            
            # NOVO: Renderiza o template de email
            email_context = {
                'otp': otp,
                'user': user,
                'email_titulo': 'Código de Recuperação de Senha'
            }
            html_message = render_to_string('Echo_app/otp_email_body.html', email_context)
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(
                    'Seu Código de Recuperação de Senha - Echo',
                    plain_message, # Corpo do e-mail em texto
                    None, # Usa DEFAULT_FROM_EMAIL
                    [email],
                    html_message=html_message, # Corpo do e-mail em HTML
                    fail_silently=False,
                )
                messages.success(request, f"Código de verificação enviado para {email}.")
            except Exception as e:
                messages.error(request, f"Erro ao enviar e-mail. Verifique a configuração SMTP. [DEBUG: {e}]")
            
            # Redireciona para a página de inserção do código (verificar_codigo)
            return redirect('Echo_app:verificar_codigo')
            
        except User.DoesNotExist:
            messages.error(request, "Este e-mail não está cadastrado.")
            
    # Template: senha.html
    return render(request, 'Echo_app/senha.html')


# ----------------------------------------------------------------------
# 2. VERIFICAR CÓDIGO (URL: /verificar-codigo/) - CORRIGIDA
# Template: Echo_app/codigo.html
# ----------------------------------------------------------------------

def verificar_codigo(request):
    # Garante que há um usuário na sessão para evitar erros
    user_pk = request.session.get('reset_user_id')
    if not user_pk:
        messages.error(request, "Sessão de redefinição expirada ou inválida. Reinicie o processo.")
        return redirect('Echo_app:iniciar_redefinicao_otp')
        
    if request.method == 'POST':
        otp_digitado = request.POST.get('codigo')
        otp_sessao = request.session.get('otp_code')
        
        if otp_sessao and str(otp_digitado) == str(otp_sessao):
            # Adiciona flag de verificação para a próxima etapa (segurança)
            request.session['otp_verified'] = True
            messages.success(request, "Código verificado com sucesso! Por favor, defina sua nova senha.")
            
            # Redireciona para a tela final de nova senha
            return redirect('Echo_app:redefinir_senha_final')
        else:
            messages.error(request, "Código inválido ou expirado.")
            
    # Template: codigo.html
    return render(request, 'Echo_app/codigo.html')


# ----------------------------------------------------------------------
# 3. REDEFINIR SENHA FINAL (URL: /redefinir-senha-final/) - CORRIGIDA
# Template: Echo_app/senha_redefinir.html
# ----------------------------------------------------------------------

# CORREÇÃO: Removido o @login_required
def redefinir_senha_final(request):
    """
    Permite ao usuário definir uma nova senha após a verificação bem-sucedida do código OTP.
    """
    
    user_pk = request.session.get('reset_user_id')
    otp_verified = request.session.get('otp_verified', False) # Verifica se o OTP foi checado
    
    if not user_pk or not otp_verified:
        messages.error(request, "Acesso negado. Por favor, complete a verificação do código.")
        return redirect('Echo_app:iniciar_redefinicao_otp')
        
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        messages.error(request, "Erro ao encontrar usuário. Reinicie o processo.")
        return redirect('Echo_app:iniciar_redefinicao_otp')
        
    if request.method == 'POST':
        # Usa o formulário nativo do Django (SetPasswordForm)
        form = SetPasswordForm(user, request.POST)
        
        if form.is_valid():
            form.save()
            
            # Limpa TODAS as chaves de sessão relacionadas
            del request.session['reset_user_id']
            if 'otp_code' in request.session:
                del request.session['otp_code']
            if 'otp_verified' in request.session:
                del request.session['otp_verified']

            # NOVO: Redireciona para a tela de conclusão (senha_concluida.html)
            messages.success(request, "Sua senha foi redefinida com sucesso!")
            return redirect('Echo_app:senha_concluida') 
        
        messages.error(request, "Erro ao redefinir a senha. Verifique se as senhas são fortes e coincidem.")
        
    else:
        form = SetPasswordForm(user)
        
    contexto = {
        'form': form,
    }
    # Template: senha_redefinir.html
    return render(request, 'Echo_app/senha_redefinir.html', contexto)


# ----------------------------------------------------------------------
# 4. TELA DE SUCESSO FINAL (URL: /senha-concluida/) - NOVA
# Template: Echo_app/senha_concluida.html
# ----------------------------------------------------------------------

def senha_concluida(request):
    # Simplesmente renderiza a tela de sucesso
    return render(request, 'Echo_app/senha_concluida.html')


# ----------------------------------------------------------------------
# 5. REENVIAR CÓDIGO - CORRIGIDA
# ----------------------------------------------------------------------

def reenviar_codigo(request):
    """
    Reenvia o código OTP usando o ID de usuário e OTP já armazenados na sessão.
    """
    user_pk = request.session.get('reset_user_id')
    otp = request.session.get('otp_code')
    
    if not user_pk or not otp:
        messages.error(request, "Sessão expirada. Por favor, reinicie a redefinição de senha.")
        return redirect('Echo_app:iniciar_redefinicao_otp')

    try:
        user = User.objects.get(pk=user_pk)
        
        # Reenvia o e-mail com o mesmo código OTP, usando o template HTML
        email_context = {
            'otp': otp,
            'user': user,
            'email_titulo': 'Reenvio de Código de Recuperação de Senha'
        }
        html_message = render_to_string('Echo_app/otp_email_body.html', email_context)
        plain_message = strip_tags(html_message)

        try:
            send_mail(
                'Reenvio do Seu Código de Recuperação de Senha - Echo',
                plain_message,
                None,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            messages.success(request, f"Um novo código foi reenviado para {user.email}.")
        except Exception:
            messages.error(request, "Erro ao tentar reenviar o e-mail. Verifique a configuração SMTP.")
            
    except User.DoesNotExist:
        messages.error(request, "Erro: Usuário não encontrado na sessão.")
    
    # Redireciona de volta para a página de verificação de código
    return redirect('Echo_app:verificar_codigo')


# ===============================================
# DASHBOARD E OUTROS (Não alterados)
# ===============================================

def dashboard(request):
    user = request.user
    categorias_interesse = []
    noticias_recomendadas_list = []

    if user.is_authenticated:
        try:
            perfil = user.perfil 
            categorias_interesse = perfil.categorias_de_interesse.all()
        except PerfilUsuario.DoesNotExist:
            perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
        noticias_recomendadas_list = Noticia.recomendar_para(user)[:3]
    else:
        noticias_recomendadas_list = Noticia.objects.order_by('-curtidas_count')[:3]
    
    try:
        urgentes_qs = Noticia.objects.filter(urgente=True).order_by('-data_publicacao')
        if noticias_recomendadas_list:
            ids_excluidos = [n.id for n in noticias_recomendadas_list]
            urgentes_qs = urgentes_qs.exclude(id__in=ids_excluidos)
        noticias_urgentes = urgentes_qs[:5] 
    except Exception:
        noticias_urgentes = None

    try:
        ultimas_noticias = Noticia.objects.filter(urgente=False).order_by('-data_publicacao')[:5]
    except Exception:
        ultimas_noticias = None
        
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
    template_name = "Echo_app/dashboard.html" if user.is_authenticated else "Echo_app/dashboard_off.html"
    return render(request, template_name, context)


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
        noticias_filtradas = None
    context = { 'ultimas_noticias': noticias_filtradas }
    return render(request, 'Echo_app/partials/lista_noticias.html', context)


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

class NoticiaDetalheView(DetailView):
    model = Noticia
    template_name = 'Echo_app/noticia_detalhe.html'
    context_object_name = 'noticia'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        noticia_atual = self.object
        user = self.request.user

        # 1. 🚨 LÓGICA DE MARCAR NOTIFICAÇÃO COMO LIDA (NOVO) 🚨
        if user.is_authenticated:
            # Pega o notif_id da query string (ex: /noticia/123?notif_id=456)
            notificacao_id = self.request.GET.get('notif_id')
            
            if notificacao_id:
                try:
                    # Busca a Notificacao específica que pertence ao usuário e está não lida
                    notificacao = Notificacao.objects.get(
                        pk=notificacao_id, 
                        usuario=user,
                        lida=False 
                    )
                    
                    # Marca como lida
                    notificacao.lida = True
                    notificacao.save()
                    
                except Notificacao.DoesNotExist:
                    # Se não encontrou (ID inválido, ou já estava lida), ignora.
                    pass
        # 2. --------------------------------------------------------

        # Lógica de Notícias Relacionadas (Mantida)
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
        
        # Lógica de Interação (Mantida)
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
        usuario=usuario, noticia=noticia, tipo=tipo_interacao
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

ITEMS_PER_PAGE = 5

@login_required
def lista_notificacoes(request):
    usuario = request.user
    categorias_preferidas = Categoria.objects.none()
    
    # Parâmetros de página para cada seção
    page_reco = request.GET.get('page_reco', 1) 
    page_lidas = request.GET.get('page_lidas', 1) 
    
    # 1. Obter Categorias de Interesse do Usuário
    try:
        perfil = usuario.perfil 
        categorias_preferidas = perfil.categorias_de_interesse.all()
    except PerfilUsuario.DoesNotExist:
        PerfilUsuario.objects.get_or_create(usuario=usuario) 
        pass
    
    # --- SEÇÃO 1: RECOMENDADAS (Notificacoes NÃO Lidas) ---
    
    # Busca Notificações não lidas E que estão vinculadas a uma Notícia
    todas_notificacoes_nao_lidas = Notificacao.objects.filter(
        usuario=usuario, 
        lida=False,
        noticia__isnull=False # Garante que só notif. de notícias sejam incluídas
    )

    if categorias_preferidas.exists():
        # Filtra as Notificações não lidas por categorias de interesse
        recomendadas_base_qs = todas_notificacoes_nao_lidas.filter(
            noticia__categoria__in=categorias_preferidas
        ).order_by('-data_criacao')
    else:
        # Se não houver categorias, mostra todas as Notificações não lidas
        recomendadas_base_qs = todas_notificacoes_nao_lidas.order_by('-data_criacao')

    # Aplicando a paginação às RECOMENDADAS (modelo Notificacao)
    paginator_reco = Paginator(recomendadas_base_qs, ITEMS_PER_PAGE)
    notificacoes_recomendadas = paginator_reco.get_page(page_reco)
    
    
    # --- SEÇÃO 2: NOTIFICAÇÕES LIDAS (Modelo Notificacao) ---
    
    # Busca TODAS as notificações do usuário que estão lidas E que estão vinculadas a uma Notícia.
    lidas_base_qs = Notificacao.objects.filter(
        usuario=usuario, 
        lida=True,
        noticia__isnull=False # Garante que só notif. de notícias sejam incluídas
    ).order_by('-data_criacao')
    
    # Aplicando a paginação às LIDAS (modelo Notificacao)
    paginator_lidas = Paginator(lidas_base_qs, ITEMS_PER_PAGE)
    notificacoes_lidas = paginator_lidas.get_page(page_lidas)
    
    
    # --- CONTAGEM DE NÃO LIDAS ---
    nao_lidas_count = todas_notificacoes_nao_lidas.count()
    
    context = {
        'notificacoes_recomendadas': notificacoes_recomendadas, # Objeto Page (Notificacao)
        'notificacoes_lidas': notificacoes_lidas,               # Objeto Page (Notificacao Lida)
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

@login_required
def perfil_detalhe(request):
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=request.user)
    context = { 'usuario': request.user, 'perfil': perfil }
    return render(request, "Echo_app/perfil.html", context)


# ===============================================
# PERFIL EDITAR COM AVATARES (Não alterado)
# ===============================================

@login_required
def perfil_editar(request):
    usuario = request.user
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=usuario)

    # Lista de nomes (avatars1.png ... avatars16.png)
    lista_avatars = [f'avatars{i}.png' for i in range(1, 17)]

    try:
        todas_categorias = Categoria.objects.all()
    except Exception:
        todas_categorias = []

    if request.method == "POST":
        erros = []
        first_name = request.POST.get("first_name", "").strip()
        email = request.POST.get("email", "").strip()
        categorias_ids = request.POST.getlist("categoria")
        biografia = request.POST.get("biografia", "").strip()
        
        foto_upload = request.FILES.get("foto_perfil") 
        avatar_escolhido = request.POST.get("avatar_escolhido")

        if not email:
            erros.append("Email é obrigatório.")
        elif User.objects.filter(email__iexact=email).exclude(pk=usuario.pk).exists():
            erros.append("Este email já está em uso por outro usuário.")

        if erros:
            context = {
                "usuario": usuario,
                "perfil": perfil,
                "todas_categorias": todas_categorias,
                "lista_avatars": lista_avatars,
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

        # Salvar Imagem
        if foto_upload:
            perfil.foto_perfil = foto_upload
        elif avatar_escolhido:
            # CORREÇÃO: Buscamos em 'static/avatars' (pasta na raiz)
            avatar_path = os.path.join(settings.BASE_DIR, 'static/avatars', avatar_escolhido)
            if os.path.exists(avatar_path):
                with open(avatar_path, 'rb') as f:
                    perfil.foto_perfil.save(avatar_escolhido, File(f), save=True)

        perfil.biografia = biografia
        perfil.save()

        return redirect("Echo_app:perfil")

    context = {
        "usuario": usuario,
        "perfil": perfil,
        "todas_categorias": todas_categorias,
        "lista_avatars": lista_avatars,
    }
    return render(request, "Echo_app/perfil_editar.html", context)


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
                "erros": erros, "titulo": titulo, "conteudo": conteudo,
                "categorias": Categoria.objects.all(), "categoria_selecionada": categoria_id,
            }
            return render(request, "Echo_app/criar_noticia.html", context)
        Noticia.objects.create(
            titulo=titulo, conteudo=conteudo, categoria=categoria,
            autor=request.user, imagem=imagem,
            urgente=request.POST.get('urgente') == 'on'
        )
        return redirect("Echo_app:dashboard")
    context = { "categorias": Categoria.objects.all() }
    return render(request, "Echo_app/criar_noticia.html", context)

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
    context = { 'form': form }
    return render(request, 'Echo_app/configuracoes.html', context)

@login_required
def noticias_curtidas(request):
    usuario = request.user
    
    # Parâmetros URL
    termo_pesquisa = request.GET.get('q', '').strip()
    categoria_nome = request.GET.get('categoria', '').strip()
    
    # Busca Base
    interacoes_qs = InteracaoNoticia.objects.filter(
        usuario=usuario, 
        tipo='CURTIDA'
    ).select_related('noticia', 'noticia__categoria').order_by('-data_interacao')
    
    # Filtro Categoria (Por NOME)
    if categoria_nome:
        interacoes_qs = interacoes_qs.filter(
            noticia__categoria__nome__iexact=categoria_nome
        )
        
    # Filtro Pesquisa
    if termo_pesquisa:
        interacoes_qs = interacoes_qs.filter(
            Q(noticia__titulo__icontains=termo_pesquisa) | 
            Q(noticia__conteudo__icontains=termo_pesquisa)
        )
        
    # Remove Duplicatas
    seen_ids = set()
    noticias_curtidas = []
    for item in interacoes_qs:
        noticia = item.noticia
        if noticia.id not in seen_ids:
            noticias_curtidas.append(noticia)
            seen_ids.add(noticia.id)

    # Categorias para o menu
    categorias_disponiveis = Categoria.objects.all().order_by('nome')

    context = {
        'noticias_curtidas': noticias_curtidas,
        'categorias_disponiveis': categorias_disponiveis, 
        'total_curtidas': len(noticias_curtidas),
        'categoria_ativa': categoria_nome 
    }
    
    return render(request, 'Echo_app/noticias_curtidas.html', context)

@login_required
def noticias_salvas_view(request):
    usuario = request.user
    termo_pesquisa = request.GET.get('q', '').strip()
    categoria_nome = request.GET.get('categoria', '').strip()

    interacoes = InteracaoNoticia.objects.filter(
        usuario=usuario, tipo='SALVAMENTO'
    ).select_related('noticia', 'noticia__categoria').order_by('-data_interacao')

    if categoria_nome:
        interacoes = interacoes.filter(noticia__categoria__nome__iexact=categoria_nome)

    if termo_pesquisa:
        interacoes = interacoes.filter(
            Q(noticia__titulo__icontains=termo_pesquisa) |
            Q(noticia__conteudo__icontains=termo_pesquisa)
        )

    seen_ids = set()
    noticias = []
    for item in interacoes:
        if item.noticia.id not in seen_ids:
            noticias.append(item.noticia)
            seen_ids.add(item.noticia.id)

    categorias_disponiveis = Categoria.objects.all().order_by('nome')

    context = {
        'noticias_salvas': noticias,
        'categorias_disponiveis': categorias_disponiveis,
        'total_salvos': len(noticias),
        'categoria_ativa': categoria_nome
    }
    return render(request, 'Echo_app/noticias_salvas.html', context)


def jogo_da_velha_view(request):
    # O template que você criou (ou irá criar) para o jogo
    return render(request, 'Echo_app/jogo_da_velha.html')

def games(request):
    """Renderiza a página hub de jogos (games.html)."""
    # Você pode adicionar contexto aqui se precisar passar dados futuros
    context = {} 
    return render(request, 'Echo_app/games.html', context)

def jogo_da_memoria(request):
    """Renderiza a página do Jogo da Memória."""
    # Como você usa subdiretórios, o nome do template é 'Echo_app/jogo_da_memoria.html'
    return render(request, 'Echo_app/jogo_da_memoria.html', {})

def jogo_da_forca(request):
    return render(request, 'Echo_app/jogo_da_forca.html')