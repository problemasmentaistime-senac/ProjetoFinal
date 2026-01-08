from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Avg
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from .models import CarrosselImagem, Categoria, Perfume, FooterInfo, PaginaEstatica, ComentarioAvaliacao, CartItem, Pedido, EnderecoEntrega, ItemPedido, Perfil
from .forms import CategoriaForm, PerfumeForm, UserUpdateForm, PerfilUpdateForm, ContactForm, ComentarioAvaliacaoForm, EnderecoForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


class SuperUserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def get_context_data(self, **kwargs):
        """Adiciona usuários ao contexto para verificar tentativas"""
        context = super().get_context_data(**kwargs)
        
        # Pega todos os usuários com perfil para verificar tentativas
        context['users'] = User.objects.select_related('perfil').all()
        
        return context
    
    def form_valid(self, form):
        """Verifica se é o primeiro login após autenticação bem-sucedida"""
        from django.contrib.auth import login as auth_login
        
        usuario = form.get_user()
        
        # Verifica se o usuário está bloqueado
        if hasattr(usuario, 'perfil'):
            perfil = usuario.perfil
            
            # Verifica se o usuário está temporariamente bloqueado
            if perfil.esta_bloqueado():
                messages.error(self.request, 
                    f"Conta temporariamente bloqueada. Tente novamente após {perfil.bloqueado_ate.strftime('%H:%M')}.")
                return self.form_invalid(form)
            
            # Reseta tentativas de erro se o login for bem-sucedido
            perfil.resetar_tentativas_erro()
        
        auth_login(self.request, form.get_user())
        
        # Verifica se é o primeiro login
        if hasattr(self.request.user, 'perfil'):
            if self.request.user.perfil.primeiro_login:
                return redirect('perfumaria:alterar_senha_inicial')
        
        return redirect(self.get_success_url())
    
    def form_invalid(self, form):
        """Contabiliza tentativas de erro de login"""
        username = form.data.get('username')
        
        if username:
            try:
                usuario = User.objects.get(username=username)
                if hasattr(usuario, 'perfil'):
                    perfil = usuario.perfil
                    perfil.incrementar_tentativa_erro()
                    
                    # Mostrar mensagem baseada no número de tentativas
                    if perfil.tentativas_erro_senha == 1:
                        messages.warning(self.request, 
                            "Primeira tentativa errada. Você tem mais 2 tentativas.")
                    elif perfil.tentativas_erro_senha == 2:
                        messages.warning(self.request, 
                            "Segunda tentativa errada. Última tentativa antes do bloqueio.")
                    elif perfil.tentativas_erro_senha >= 3:
                        messages.error(self.request, 
                            "Você excedeu o número máximo de tentativas. "
                            "Conta bloqueada por 15 minutos. "
                            "Após o desbloqueio, será necessário alterar sua senha.")
        
            except User.DoesNotExist:
                # Usuário não existe, não faz nada
                pass
        
        return super().form_invalid(form)


@csrf_exempt
def reset_password_ajax(request):
    """View AJAX para redefinir senha diretamente na página de login"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        new_password1 = request.POST.get('new_password1', '').strip()
        new_password2 = request.POST.get('new_password2', '').strip()
        
        # Validações básicas
        if not email or not new_password1 or not new_password2:
            return JsonResponse({
                'success': False,
                'message': 'Todos os campos são obrigatórios.'
            })
        
        # Verificar se as senhas coincidem
        if new_password1 != new_password2:
            return JsonResponse({
                'success': False,
                'message': 'As senhas não coincidem.'
            })
        
        # Validar força da senha
        if len(new_password1) < 8:
            return JsonResponse({
                'success': False,
                'message': 'A senha deve ter no mínimo 8 caracteres.'
            })
        
        # Verificar se o e-mail existe no sistema
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'E-mail não encontrado no sistema.'
            })
        
        # Alterar a senha
        try:
            user.set_password(new_password1)
            user.save()
            
            # Resetar tentativas de erro no perfil
            if hasattr(user, 'perfil'):
                user.perfil.resetar_tentativas_erro()
                user.perfil.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Senha redefinida com sucesso! Agora você pode fazer login com a nova senha.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao redefinir senha: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido.'
    })


@login_required
def alterar_senha_inicial(request):
    """View para obrigar o usuário a alterar sua senha no primeiro login"""
    
    # Verifica se o usuário já alterou a senha
    if hasattr(request.user, 'perfil'):
        if not request.user.perfil.primeiro_login:
            messages.info(request, "Você já alterou sua senha anteriormente.")
            return redirect('home')
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Mantém o usuário logado
            
            # Marca que o primeiro login foi concluído
            if hasattr(request.user, 'perfil'):
                request.user.perfil.marcar_senha_alterada()
            
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('home')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'registration/alterar_senha_inicial.html', {
        'form': form,
        'obrigatorio': True,  # Flag para mostrar que é obrigatório
        'footer_info': FooterInfo.objects.first()
    })


@login_required
def alterar_senha(request):
    """View para o usuário alterar sua senha quando quiser (normal ou obrigatório)"""
    
    # Verificar se precisa alterar senha por tentativas erradas
    precisa_alterar = False
    if hasattr(request.user, 'perfil'):
        precisa_alterar = request.user.perfil.precisa_alterar_senha()
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Mantém o usuário logado
            
            # Reseta as tentativas de erro quando a senha é alterada com sucesso
            if hasattr(request.user, 'perfil'):
                request.user.perfil.marcar_senha_alterada()
            
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('perfumaria:perfil')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'registration/alterar_senha.html', {
        'form': form,
        'obrigatorio': precisa_alterar,  # Flag para mostrar se é obrigatório
        'footer_info': FooterInfo.objects.first()
    })


def home(request):
    imagens_carrossel = CarrosselImagem.objects.filter(ativo=True).order_by('ordem')[:3]
    imagens_list = list(imagens_carrossel)
    while len(imagens_list) < 3:
        imagens_list.append({
            'titulo': f'Novidade {len(imagens_list) + 1}',
            'descricao': 'Em breve mais informações',
            'imagem': None,
            'id': len(imagens_list) + 100
        })
    categorias = Categoria.objects.all()[:3]
    perfumes_destaque = Perfume.objects.filter(destaque=True)[:3]
    footer_info = FooterInfo.objects.first()
    
    context = {
        'imagens_carrossel': imagens_list,
        'categorias': categorias,
        'perfumes_destaque': perfumes_destaque,
        'footer_info': footer_info,
    }
    return render(request, 'perfumaria/home.html', context)


def produtos(request):
    categoria_id = request.GET.get('categoria')
    
    if categoria_id:
        try:
            categoria = Categoria.objects.get(id=categoria_id)
            produtos_lista = Perfume.objects.filter(categoria=categoria).order_by('-data_cadastro')
            categoria_selecionada = categoria
        except Categoria.DoesNotExist:
            produtos_lista = Perfume.objects.all().order_by('-data_cadastro')
            categoria_selecionada = None
    else:
        produtos_lista = Perfume.objects.all().order_by('-data_cadastro')
        categoria_selecionada = None
    
    footer_info = FooterInfo.objects.first()
    
    context = {
        'perfumes': produtos_lista,
        'categoria_selecionada': categoria_selecionada,
        'footer_info': footer_info,
    }
    return render(request, 'perfumaria/produtos.html', context)


def produtos_por_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    produtos_lista = Perfume.objects.filter(categoria=categoria).order_by('-data_cadastro')
    footer_info = FooterInfo.objects.first()
    
    context = {
        'perfumes': produtos_lista,
        'categoria_selecionada': categoria,
        'footer_info': footer_info,
    }
    return render(request, 'perfumaria/produtos.html', context)


def politica_privacidade(request):
    pagina = PaginaEstatica.objects.filter(
        tipo_pagina='PRIVACIDADE', 
        ativo=True
    ).first()
    if pagina:
        titulo = pagina.titulo
        conteudo = pagina.conteudo
    else:
        titulo = "Política de Privacidade"
        conteudo = """
        <div style="color: #cccccc; line-height: 1.8;">
            <h2 style="color: #D4AF37;">Política de Privacidade da Perfumaria Lux</h2>
            <p>Esta página está em construção. O conteúdo completo estará disponível em breve.</p>
            <p>Para mais informações, entre em contato através dos canais disponíveis no rodapé.</p>
        </div>
        """
    footer_info = FooterInfo.objects.first()
    context = {
        'titulo': titulo,
        'conteudo': conteudo,
        'footer_info': footer_info,
    }
    return render(request, 'perfumaria/politica-privacidade.html', context)


def politica_devolucao(request):
    pagina = PaginaEstatica.objects.filter(
        tipo_pagina='DEVOLUCAO', 
        ativo=True
    ).first()
    if pagina:
        titulo = pagina.titulo
        conteudo = pagina.conteudo
    else:
        titulo = "Política de Devolução e Trocas"
        conteudo = """
        <div style="color: #cccccc; line-height: 1.8; text-align: center; padding: 50px;">
            <h2 style="color: #D4AF37;">Política de Devolução da Perfumaria Lux</h2>
            <p>Esta página está em construção. O conteúdo completo estará disponível em breve.</p>
            <p>Para mais informações sobre devoluções, entre em contato através dos canais disponíveis no rodapé.</p>
        </div>
        """
    footer_info = FooterInfo.objects.first()
    context = {
        'titulo': titulo,
        'conteudo': conteudo,
        'footer_info': footer_info,
    }
    return render(request, 'perfumaria/politica-devolucao.html', context)


def termos_uso(request):
    pagina = PaginaEstatica.objects.filter(
        tipo_pagina='TERMOS', 
        ativo=True
    ).first()
    if pagina:
        titulo = pagina.titulo
        conteudo = pagina.conteudo
    else:
        titulo = "Termos de Uso"
        conteudo = """
        <div style="color: #cccccc; line-height: 1.8; text-align: center; padding: 50px;">
            <h2 style="color: #D4AF37;">Termos de Uso da Perfumaria Lux</h2>
            <p>Esta página está em construção. Os termos completos estarão disponíveis em breve.</p>
            <p>Para mais informações, entre em contato através dos canais disponíveis no rodapé.</p>
        </div>
        """
    footer_info = FooterInfo.objects.first()
    context = {
        'titulo': titulo,
        'conteudo': conteudo,
        'footer_info': footer_info,
    }
    return render(request, 'perfumaria/termos-uso.html', context)


def sobre(request):
    pagina = PaginaEstatica.objects.filter(
        tipo_pagina='SOBRE', 
        ativo=True
    ).first()
    if pagina:
        titulo = pagina.titulo
        conteudo = pagina.conteudo
    else:
        titulo = "Sobre Nós"
        conteudo = """
        <div style="color: #cccccc; line-height: 1.8; text-align: center; padding: 50px;">
            <h2 style="color: #D4AF37;">Conheça a Perfumaria Lux</h2>
            <p>Esta página está em construção. Em breve teremos informações completas sobre nossa história.</p>
            <p>Para mais informações, entre em contato através dos canais disponíveis no rodapé.</p>
        </div>
        """
    footer_info = FooterInfo.objects.first()
    context = {
        'titulo': titulo,
        'conteudo': conteudo,
        'footer_info': footer_info,
    }
    return render(request, 'perfumaria/sobre.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Processa o formulário de contato
            nome = form.cleaned_data.get('nome', '')
            email = form.cleaned_data.get('email', '')
            mensagem = form.cleaned_data.get('mensagem', '')
            
            # Adiciona uma mensagem de sucesso
            messages.success(request, 'Sua mensagem foi enviada com sucesso!')
            
            return redirect('perfumaria:success')  # ← LINHA 264 CORRIGIDA: adicionei 'perfumaria:'
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


def criarconta(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Garante que o perfil seja criado com primeiro_login=True
            Perfil.objects.get_or_create(
                user=user, 
                defaults={
                    'primeiro_login': True,
                    'imagem': 'perfil_padrao.jpg'
                }
            )
            
            messages.success(request, "Conta criada com sucesso! Bem-vindo!")
            return redirect('perfumaria:alterar_senha_inicial')  # Redireciona para alterar senha
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = UserCreationForm()
    
    footer_info = FooterInfo.objects.first()
    context = {
        'form': form,
        'footer_info': footer_info,
    }
    return render(request, 'registration/criarconta.html', context)


def success(request):
    return render(request, 'success.html')


def confirma(request):
    cart_items = CartItem.objects.filter(user=request.user)
    cart_items.delete()
    return render(request, 'perfumaria/confirma.html')


def pagina_estatica(request, tipo):
    tipo_map = {
        'faq': 'FAQ',
        'garantia': 'GARANTIA',
        'trocas': 'TROCAS',
    }
    tipo_pagina = tipo_map.get(tipo, 'OUTROS')
    pagina = PaginaEstatica.objects.filter(
        tipo_pagina=tipo_pagina, 
        ativo=True
    ).first()
    if pagina:
        titulo = pagina.titulo
        conteudo = pagina.conteudo
    else:
        titulo = tipo.replace('-', ' ').title()
        conteudo = f"<p style='color: #ccc; text-align: center; padding: 50px;'>Página {titulo} em construção...</p>"
    footer_info = FooterInfo.objects.first()
    context = {
        'titulo': titulo,
        'conteudo': conteudo,
        'footer_info': footer_info,
    }
    return render(request, 'perfumaria/pagina-estatica.html', context)


@login_required
def painel_admin_redirect(request):
    if request.user.is_superuser:
        return redirect('painel_admin')
    else:
        return redirect('home')


class PainelAdminView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    template_name = 'perfumaria/painel_admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_categorias'] = Categoria.objects.count()
        context['total_perfumes'] = Perfume.objects.count()
        context['perfumes_destaque'] = Perfume.objects.filter(destaque=True).count()
        context['ultimos_perfumes'] = Perfume.objects.all().order_by('-data_cadastro')[:5]
        context['produtos_sem_estoque'] = Perfume.objects.filter(estoque__lte=0).count()
        return context


class CategoriaListView(LoginRequiredMixin, SuperUserRequiredMixin, ListView):
    model = Categoria
    template_name = 'perfumaria/painel_admin/categoria_list.html'
    context_object_name = 'categorias'
    ordering = ['ordem']


class CategoriaCreateView(LoginRequiredMixin, SuperUserRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'perfumaria/painel_admin/categoria_form.html'
    success_url = reverse_lazy('categoria_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Categoria criada com sucesso!")
        return super().form_valid(form)
    
    
    def form_invalid(self, form):
        messages.error(self.request, "Erro ao criar categoria. Verifique os dados.")
        return super().form_invalid(form)


class CategoriaUpdateView(LoginRequiredMixin, SuperUserRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'perfumaria/painel_admin/categoria_form.html'
    success_url = reverse_lazy('categoria_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Categoria atualizada com sucesso!")
        return super().form_valid(form)
    
    
    def form_invalid(self, form):
        messages.error(self.request, "Erro ao atualizar categoria. Verifique os dados.")
        return super().form_invalid(form)


class CategoriaDeleteView(LoginRequiredMixin, SuperUserRequiredMixin, DeleteView):
    model = Categoria
    template_name = 'perfumaria/painel_admin/categoria_confirm_delete.html'
    success_url = reverse_lazy('categoria_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Categoria excluída com sucesso!")
        return super().delete(request, *args, **kwargs)


class PerfumeListView(LoginRequiredMixin, SuperUserRequiredMixin, ListView):
    model = Perfume
    template_name = 'perfumaria/painel_admin/perfume_list.html'
    context_object_name = 'perfumes'
    ordering = ['-data_cadastro']


class PerfumeCreateView(LoginRequiredMixin, SuperUserRequiredMixin, CreateView):
    model = Perfume
    form_class = PerfumeForm
    template_name = 'perfumaria/painel_admin/perfume_form.html'
    success_url = reverse_lazy('perfume_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Perfume criado com sucesso!")
        return super().form_valid(form)
    
    
    def form_invalid(self, form):
        messages.error(self.request, "Erro ao criar perfume. Verifique os dados.")
        return super().form_invalid(form)
    
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')
        return form


class PerfumeUpdateView(LoginRequiredMixin, SuperUserRequiredMixin, UpdateView):
    model = Perfume
    form_class = PerfumeForm
    template_name = 'perfumaria/painel_admin/perfume_form.html'
    success_url = reverse_lazy('perfume_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Perfume atualizado com sucesso!")
        return super().form_valid(form)
    
    
    def form_invalid(self, form):
        messages.error(self.request, "Erro ao atualizar perfume. Verifique os dados.")
        return super().form_invalid(form)
    
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')
        return form


class PerfumeDeleteView(LoginRequiredMixin, SuperUserRequiredMixin, DeleteView):
    model = Perfume
    template_name = 'perfumaria/painel_admin/perfume_confirm_delete.html'
    success_url = reverse_lazy('perfume_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Perfume excluído com sucesso!")
        return super().delete(request, *args, **kwargs)


@login_required # Garante que o usuário esteja logado para acessar esta view
def perfil(request):
    # Verificar se precisa alterar senha por tentativas erradas
    precisa_alterar_senha = False
    tentativas_erro = 0
    
    if hasattr(request.user, 'perfil'):
        precisa_alterar_senha = request.user.perfil.precisa_alterar_senha()
        tentativas_erro = request.user.perfil.tentativas_erro_senha
    
    if request.method == 'POST':
        # Popula os formulários com os dados enviados pelo POST e instâncias existentes
        u_form = UserUpdateForm(request.POST, instance=request.user) 
        p_form = PerfilUpdateForm(request.POST, request.FILES, instance=request.user.perfil)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Seu perfil foi atualizado com sucesso!')
            return redirect('perfumaria:perfil') # Redireciona para evitar reenvio do formulário
        else:
            messages.error(request, 'Ocorreu um erro ao atualizar seu perfil. Verifique os dados.')

    else: # Se a requisição for GET (primeira vez que a página é acessada)
        u_form = UserUpdateForm(instance=request.user)
        p_form = PerfilUpdateForm(instance=request.user.perfil)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'precisa_alterar_senha': precisa_alterar_senha,
        'tentativas_erro': tentativas_erro,
    }
    
    return render(request, 'perfumaria/perfil.html', context)


class PerfumeDetailView(DetailView):
    model = Perfume
    template_name = "perfumaria/perfume_detail.html"
    context_object_name = "perfume"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_comentario'] = ComentarioAvaliacaoForm()
        context['total_comentarios'] = self.object.comentarios.count()
        if self.object.comentarios.exists():
            context['avaliacao_media'] = self.object.comentarios.aggregate(
                media=Avg('avaliacao')  # <--- usar Avg direto
            )['media']
        else:
           context['avaliacao_media'] = 0

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ComentarioAvaliacaoForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.produto = self.object
            comentario.cliente = request.user
            comentario.save()
            return redirect('perfumaria:produto_detail', pk=self.object.pk)
        context = self.get_context_data(form_comentario=form)
        return self.render_to_response(context)


def product_list(request):
    products = Perfume.objects.all()
    return render(request, 'perfumaria/index.html', {'products': products})


@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.product.preco * item.quantity for item in cart_items)
    return render(request, 'perfumaria/cart.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def add_to_cart(request, product_id):
    product = Perfume.objects.get(id=product_id)
    cart_item, created = CartItem.objects.get_or_create(product=product, 
                                                       user=request.user)
    cart_item.quantity += 1
    cart_item.save()
    return redirect('perfumaria:view_cart')


def remove_from_cart(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    cart_item.delete()
    return redirect('perfumaria:view_cart')


def endereco_entrega(request):
    if request.method == "POST":
        form = EnderecoForm(request.POST)
        if form.is_valid():
            endereco = form.save(commit=False)
            endereco.cliente = request.user
            endereco.save()
            return redirect("perfumaria:confirma")
        else:
            print(form.errors)

    else:
        form = EnderecoForm()

    return render(
        request,
        "perfumaria/endereco.html",
        {"form": form}
    )


def finalizar_compra(request):
    if request.method == "POST":
        endereco = EnderecoEntrega.objects.filter(cliente=request.user).first()
        cart_items = CartItem.objects.filter(user=request.user)

        pedido = Pedido.objects.create(
            cliente=request.user,
            endereco_entrega=endereco,
            status="P"
        )

        for item in cart_items:
            produto = item.product
            ItemPedido.objects.create(
                pedido=pedido,
                produto=item.product,
                quantity=item.quantity,
                preco=item.product.preco
        )

            if produto.estoque < item.quantity:
                messages.error(
                    request,
                    f"Estoque insuficiente para {produto.nome}"
                )
                raise Exception("Estoque insuficiente")

            produto.estoque -= item.quantity
            produto.save()

            item.pedido = pedido
            item.save()

        messages.success(request, "Compra finalizada com sucesso!")
        return redirect("perfumaria:endereco")

    return redirect("perfumaria:endereco")


def lista_pedidos(request):
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-data_pedido')
    return render(request, 'perfumaria/lista_pedidos.html', {'pedidos': pedidos})


def detalhe_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=request.user)
    return render(request, 'perfumaria/detalhe_pedido.html', {'pedido': pedido})

def logout_admin(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('perfumaria:home')