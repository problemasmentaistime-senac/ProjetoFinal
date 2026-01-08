from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Categoria, Perfume, CarrosselImagem, FooterInfo, PaginaEstatica, ItemPedido, Pedido

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ordem']
    list_editable = ['ordem']

@admin.register(Perfume)
class PerfumeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'categoria', 'destaque', 'estoque']
    list_filter = ['categoria', 'destaque']
    list_editable = ['destaque', 'estoque']
    search_fields = ['nome']
    
    # SIMPLIFIQUEI OS FIELDSETS - REMOVI A IMAGEM PREVIEW DO FORMULÁRIO
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'preco', 'categoria', 'destaque', 'imagem', 'estoque')
        }),
    )
    
    readonly_fields = ('data_cadastro',)
    
    #  A LISTA
    def imagem_admin(self, obj):
        if obj and obj.imagem:
            try:
                return mark_safe(f'<img src="{obj.imagem.url}" width="50" style="border-radius: 4px;" />')
            except:
                return "-"
        return "-"
    imagem_admin.short_description = 'Imagem'
    
   
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.imagem:  # Se existe e tem imagem, mostra preview
            readonly_fields.append('imagem_preview_simple')
        return readonly_fields
    
    def imagem_preview_simple(self, obj):
        """Método simplificado que só é adicionado quando obj existe"""
        if obj and obj.imagem:
            try:
                return mark_safe(f'''
                    <div style="margin-top: 10px;">
                        <strong>Pré-visualização:</strong><br>
                        <img src="{obj.imagem.url}" width="200" style="border: 1px solid #ddd; margin-top: 5px;" />
                    </div>
                ''')
            except:
                return "Erro ao carregar imagem"
        return "Sem imagem para visualizar"
    imagem_preview_simple.short_description = 'Visualização da Imagem'
    
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        if obj:  
            
            fieldsets += (
                ('Informações Técnicas', {
                    'fields': ('data_cadastro',),
                    'classes': ('collapse',),
                }),
            )
            
            
            if obj.imagem:
                fieldsets = (
                    ('Informações Básicas', {
                        'fields': ('nome', 'descricao', 'preco', 'categoria', 'destaque')
                    }),
                    ('Imagem', {
                        'fields': ('imagem', 'imagem_preview_simple'),
                        'classes': ('collapse', 'wide'),
                    }),
                    ('Informações Técnicas', {
                        'fields': ('data_cadastro',),
                        'classes': ('collapse',),
                    }),
                )
        
        return fieldsets

@admin.register(CarrosselImagem)
class CarrosselImagemAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'ordem', 'ativo']
    list_editable = ['ordem', 'ativo']

@admin.register(FooterInfo)
class FooterInfoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'data_atualizacao']
    readonly_fields = ['data_atualizacao']
    
    fieldsets = (
        ('Informações Gerais', {
            'fields': ('titulo', 'descricao')
        }),
        ('Links de Políticas', {
            'fields': ('link_politicas_devolucao', 'link_politicas_privacidade', 'link_termos_uso'),
            'classes': ('collapse',)
        }),
        ('Redes Sociais', {
            'fields': ('linkedin_url', 'instagram_url', 'twitter_url'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PaginaEstatica)
class PaginaEstaticaAdmin(admin.ModelAdmin):
    list_display = ['tipo_pagina_display', 'titulo', 'data_atualizacao', 'ativo', 'preview_link']
    list_editable = ['titulo', 'ativo']
    list_filter = ['tipo_pagina', 'ativo']
    readonly_fields = ['data_atualizacao']
    search_fields = ['titulo', 'conteudo']
    
    def tipo_pagina_display(self, obj):
        return obj.get_tipo_pagina_display()
    tipo_pagina_display.short_description = 'Tipo de Página'
    
    def preview_link(self, obj):
        url_map = {
            'PRIVACIDADE': '/politica-privacidade/',
            'TERMOS': '/termos-uso/',
            'SOBRE': '/sobre/',
            'CONTATO': '/contato/',
            'DEVOLUCAO': '/politica-devolucao/',
        }
        url = url_map.get(obj.tipo_pagina, '#')
        if url == '#':
            return "N/A"
        
        return format_html(
            '<a href="{}" target="_blank" style="background: #4CAF50; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;">Ver no Site</a>',
            url
        )
    preview_link.short_description = 'Visualizar'
    
    fieldsets = (
        ('Configurações da Página', {
            'fields': ('tipo_pagina', 'titulo', 'ativo')
        }),
        ('Conteúdo da Página', {
            'fields': ('conteudo',),
            'description': 'Use HTML para formatação ou texto simples.'
        }),
        ('Informações Técnicas', {
            'fields': ('data_atualizacao',),
            'classes': ('collapse',)
        }),
    )

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ("produto", "quantity", "preco")
    can_delete = False

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "status", "data_pedido", "total_pedido")
    list_filter = ("status", "data_pedido")
    search_fields = ("cliente__username", "id")
    inlines = [ItemPedidoInline]
    readonly_fields = ("data_pedido",)

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "produto", "quantity", "preco")
    search_fields = ("pedido__id", "produto__nome")