from django.apps import apps

def categorias_context(request):
    """
    Context processor que fornece categorias e informações do footer
    para todos os templates.
    """
    Categoria = apps.get_model('perfumaria', 'Categoria')
    FooterInfo = apps.get_model('perfumaria', 'FooterInfo')
    
    # Tenta pegar categorias
    try:
        categorias = Categoria.objects.all().order_by('ordem')
    except Exception:
        categorias = []
    
    # Tenta pegar footer info
    try:
        footer_info = FooterInfo.objects.first()
    except Exception:
        footer_info = None
    
    return {
        'categorias': categorias,
        'footer_info': footer_info,
    }

def pedidos_admin_context(request):
    """
    Context processor que fornece a contagem de pedidos para o painel admin.
    Apenas para superusuários.
    """
    # Verifica se o usuário está autenticado e é superusuário
    if request.user.is_authenticated and request.user.is_superuser:
        Pedido = apps.get_model('perfumaria', 'Pedido')
        
        try:
            total_pedidos = Pedido.objects.count()
            pedidos_pendentes = Pedido.objects.filter(status='P').count()
            
            return {
                'total_pedidos': total_pedidos,
                'pedidos_pendentes': pedidos_pendentes,
                'admin_stats': {
                    'total_pedidos': total_pedidos,
                    'pedidos_pendentes': pedidos_pendentes,
                    'pedidos_pagos': Pedido.objects.filter(status='PA').count(),
                    'pedidos_enviados': Pedido.objects.filter(status='E').count(),
                }
            }
        except Exception:
            return {
                'total_pedidos': 0,
                'pedidos_pendentes': 0,
                'admin_stats': {
                    'total_pedidos': 0,
                    'pedidos_pendentes': 0,
                    'pedidos_pagos': 0,
                    'pedidos_enviados': 0,
                }
            }
    
    # Retorna valores padrão para usuários não-admin
    return {
        'total_pedidos': 0,
        'pedidos_pendentes': 0,
        'admin_stats': None
    }

def user_pedidos_context(request):
    """
    Context processor que fornece informações de pedidos do usuário logado.
    """
    if request.user.is_authenticated:
        Pedido = apps.get_model('perfumaria', 'Pedido')
        
        try:
            meus_pedidos_count = Pedido.objects.filter(cliente=request.user).count()
            meus_pedidos_pendentes = Pedido.objects.filter(cliente=request.user, status='P').count()
            
            return {
                'meus_pedidos_count': meus_pedidos_count,
                'meus_pedidos_pendentes': meus_pedidos_pendentes,
                'ultimos_pedidos': Pedido.objects.filter(cliente=request.user).order_by('-data_pedido')[:3]
            }
        except Exception:
            return {
                'meus_pedidos_count': 0,
                'meus_pedidos_pendentes': 0,
                'ultimos_pedidos': []
            }
    
    return {
        'meus_pedidos_count': 0,
        'meus_pedidos_pendentes': 0,
        'ultimos_pedidos': []
    }