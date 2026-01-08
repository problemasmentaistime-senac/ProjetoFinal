from django.shortcuts import redirect
from django.urls import reverse

class VerificarPrimeiroLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verifica se o usuário está autenticado
        if request.user.is_authenticated:
            # URLs que o usuário pode acessar mesmo sem alterar a senha
            urls_permitidas = [
                reverse('perfumaria:alterar_senha_inicial'),
                reverse('logout'),
                reverse('login'),
                reverse('signup'),
            ]
            
            # Verifica se é o primeiro login
            if hasattr(request.user, 'perfil'):
                if request.user.perfil.primeiro_login:
                    # Se não estiver tentando acessar uma URL permitida, redireciona
                    if request.path not in urls_permitidas:
                        return redirect('perfumaria:alterar_senha_inicial')
        
        response = self.get_response(request)
        return response