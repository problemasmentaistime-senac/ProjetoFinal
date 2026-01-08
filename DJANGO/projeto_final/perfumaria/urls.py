from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from . import views
from django import forms
from django.db import models
from .models import Categoria, Perfume, Pedido

app_name = 'perfumaria'


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'slug', 'ordem']  
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PerfumeForm(forms.ModelForm):
    class Meta:
        model = Perfume
        fields = ['nome', 'categoria', 'descricao', 'preco', 'estoque', 'destaque', 'imagem']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'estoque': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Quantidade em estoque'
            }),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'estoque': 'Quantidade em Estoque',
        }
        help_texts = {
            'estoque': 'Digite a quantidade disponível em estoque (não pode ser negativo)',
        }
    
    def clean_estoque(self):
        """Validação para garantir que o estoque não seja negativo"""
        estoque = self.cleaned_data.get('estoque')
        if estoque is not None and estoque < 0:
            raise forms.ValidationError("O estoque não pode ser negativo.")
        return estoque
    
    def clean_preco(self):
        """Validação para garantir que o preço seja positivo"""
        preco = self.cleaned_data.get('preco')
        if preco is not None and preco <= 0:
            raise forms.ValidationError("O preço deve ser maior que zero.")
        return preco

# Form para atualizar status do pedido
class PedidoStatusForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class PainelAdminView(views.ListView):
    model = Perfume
    template_name = 'perfumaria/painel_admin/dashboard.html'  
    context_object_name = 'ultimos_perfumes'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_categorias'] = Categoria.objects.count()
        context['total_perfumes'] = Perfume.objects.count()
        context['perfumes_destaque'] = Perfume.objects.filter(destaque=True).count()
        context['ultimos_perfumes'] = Perfume.objects.order_by('-data_cadastro')[:5]
        return context

class CategoriaListView(views.ListView):
    model = Categoria
    template_name = 'perfumaria/painel_admin/categoria_list.html'  
    context_object_name = 'categorias'

class CategoriaCreateView(views.CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'perfumaria/painel_admin/categoria_form.html'  
    success_url = reverse_lazy('perfumaria:categoria_list')  # CORRIGIDO
    
    def form_valid(self, form):
        messages.success(self.request, 'Categoria criada com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao criar categoria. Verifique os dados.')
        return super().form_invalid(form)

class CategoriaUpdateView(views.UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'perfumaria/painel_admin/categoria_form.html'  
    success_url = reverse_lazy('perfumaria:categoria_list')  # CORRIGIDO
    
    def form_valid(self, form):
        messages.success(self.request, 'Categoria atualizada com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao atualizar categoria. Verifique os dados.')
        return super().form_invalid(form)

class CategoriaDeleteView(views.DeleteView):
    model = Categoria
    template_name = 'perfumaria/painel_admin/categoria_confirm_delete.html'  
    success_url = reverse_lazy('perfumaria:categoria_list')  # CORRIGIDO
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Categoria excluída com sucesso!')
        return super().delete(request, *args, **kwargs)

class PerfumeListView(views.ListView):
    model = Perfume
    template_name = 'perfumaria/painel_admin/perfume_list.html'  
    context_object_name = 'perfumes'

class PerfumeCreateView(views.CreateView):
    model = Perfume
    form_class = PerfumeForm
    template_name = 'perfumaria/painel_admin/perfume_form.html'  
    success_url = reverse_lazy('perfumaria:perfume_list')  # CORRIGIDO
    
    def form_valid(self, form):
        messages.success(self.request, 'Perfume criado com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao criar perfume. Verifique os dados.')
        return super().form_invalid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')
        return form

class PerfumeUpdateView(views.UpdateView):
    model = Perfume
    form_class = PerfumeForm
    template_name = 'perfumaria/painel_admin/perfume_form.html'  
    success_url = reverse_lazy('perfumaria:perfume_list')  # CORRIGIDO
    
    def form_valid(self, form):
        messages.success(self.request, 'Perfume atualizado com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao atualizar perfume. Verifique os dados.')
        return super().form_invalid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')
        return form

class PerfumeDeleteView(views.DeleteView):
    model = Perfume
    template_name = 'perfumaria/painel_admin/perfume_confirm_delete.html'  
    success_url = reverse_lazy('perfumaria:perfume_list')  # CORRIGIDO
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Perfume excluído com sucesso!')
        return super().delete(request, *args, **kwargs)

# Views para pedidos no painel admin
class PedidoListView(views.ListView):
    model = Pedido
    template_name = 'perfumaria/painel_admin/pedido_list.html'
    context_object_name = 'pedidos'
    ordering = ['-data_pedido']
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtro por cliente (busca)
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                models.Q(cliente__username__icontains=search_query) |
                models.Q(cliente__first_name__icontains=search_query) |
                models.Q(cliente__email__icontains=search_query) |
                models.Q(id__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_pedidos'] = Pedido.objects.count()
        context['pedidos_pendentes'] = Pedido.objects.filter(status='P').count()
        context['pedidos_pagos'] = Pedido.objects.filter(status='PA').count()
        context['pedidos_enviados'] = Pedido.objects.filter(status='E').count()
        context['STATUS_CHOICES'] = Pedido.STATUS_CHOICES
        return context

class PedidoDetailView(views.DetailView):
    model = Pedido
    template_name = 'perfumaria/painel_admin/pedido_detail.html'
    context_object_name = 'pedido'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['STATUS_CHOICES'] = Pedido.STATUS_CHOICES
        return context

class PedidoUpdateView(views.UpdateView):
    model = Pedido
    form_class = PedidoStatusForm
    template_name = 'perfumaria/painel_admin/pedido_update.html'
    success_url = reverse_lazy('perfumaria:admin_pedido_list')  # CORRIGIDO
    
    def form_valid(self, form):
        messages.success(self.request, "Status do pedido atualizado com sucesso!")
        return super().form_valid(form)


# Importe as views customizadas que criamos
from django.contrib.auth.views import LoginView
from .views import CustomLoginView
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    # URL de login customizada (substitui a padrão do Django)
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    
    # URL para alteração de senha inicial (obrigatória)
    path('alterar-senha-inicial/', views.alterar_senha_inicial, name='alterar_senha_inicial'),
    
    # URL para alteração de senha normal (no perfil)
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),
    
    # URL para redefinição de senha via AJAX (na página de login)
    path('reset-password-ajax/', csrf_exempt(views.reset_password_ajax), name='reset_password_ajax'),
    
    # Suas URLs existentes (mantidas intactas)
    path('', views.home, name='home'),
    path('produtos/', views.produtos, name='produtos'),
    path('produtos/categoria/<int:categoria_id>/', views.produtos_por_categoria, name='produtos_por_categoria'),
    path('politica-privacidade/', views.politica_privacidade, name='politica_privacidade'),
    path('politica-devolucao/', views.politica_devolucao, name='politica_devolucao'),
    path('termos-uso/', views.termos_uso, name='termos_uso'),
    path('sobre/', views.sobre, name='sobre'),
    path('contact/', views.contact, name='contact'),
    path('success/', views.success, name='success'),
    path('pagina/<str:tipo>/', views.pagina_estatica, name='pagina_estatica'),
    path('perfil/', views.perfil, name='perfil'),
    path("produtos/<int:pk>/", views.PerfumeDetailView.as_view(), name="produto_detail"),
    path('confirma/', views.confirma, name='confirma'),
    path('endereco/', views.endereco_entrega, name='endereco'),
    path('cart/', views.view_cart, name='view_cart'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('finalizar_compra/', views.finalizar_compra, name='clear_cart'),
    path('painel-admin/', login_required(PainelAdminView.as_view()), name='painel_admin'),
    path('logout_admin/', views.logout_admin, name='logout_admin'),
    path('painel-admin/redirect/', views.painel_admin_redirect, name='painel_admin_redirect'),
    path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
    path('pedidos/<int:pedido_id>/', views.detalhe_pedido, name='detalhe_pedido'),
    
    path('painel-admin/categorias/', login_required(CategoriaListView.as_view()), name='categoria_list'),
    path('painel-admin/categorias/nova/', login_required(CategoriaCreateView.as_view()), name='categoria_create'),
    path('painel-admin/categorias/editar/<int:pk>/', login_required(CategoriaUpdateView.as_view()), name='categoria_update'),
    path('painel-admin/categorias/excluir/<int:pk>/', login_required(CategoriaDeleteView.as_view()), name='categoria_delete'),
    
    path('painel-admin/perfumes/', login_required(PerfumeListView.as_view()), name='perfume_list'),
    path('painel-admin/perfumes/novo/', login_required(PerfumeCreateView.as_view()), name='perfume_create'),
    path('painel-admin/perfumes/editar/<int:pk>/', login_required(PerfumeUpdateView.as_view()), name='perfume_update'),
    path('painel-admin/perfumes/excluir/<int:pk>/', login_required(PerfumeDeleteView.as_view()), name='perfume_delete'),
    
    # URLs para gerenciamento de pedidos no painel admin
    path('painel-admin/pedidos/', login_required(PedidoListView.as_view()), name='admin_pedido_list'),
    path('painel-admin/pedidos/<int:pk>/', login_required(PedidoDetailView.as_view()), name='admin_pedido_detail'),
    path('painel-admin/pedidos/<int:pk>/atualizar/', login_required(PedidoUpdateView.as_view()), name='admin_pedido_update'),
]