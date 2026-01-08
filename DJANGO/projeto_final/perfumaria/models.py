from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from PIL import Image
from django.utils import timezone


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True)
    ordem = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['ordem']
    
    def __str__(self):
        return self.nome

class Perfume(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='perfumes')
    estoque = models.SmallIntegerField(default=0)  # Adicione default=0
    
    imagem = models.ImageField(
        upload_to='perfumes/', 
        blank=True, 
        null=True,
        verbose_name="Foto do Perfume",
        help_text="Formatos suportados: JPG, PNG, GIF. Tamanho máximo: 5MB"
    )
    
    destaque = models.BooleanField(default=False)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nome
    
    def tem_imagem(self):
        return bool(self.imagem)
    
    def imagem_url(self):
        if self.imagem and hasattr(self.imagem, 'url'):
            return self.imagem.url
        return None
    
    def em_estoque(self):
        """Verifica se o produto está em estoque"""
        return self.estoque > 0

class CarrosselImagem(models.Model):
    titulo = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to='carrossel/', blank=True, null=True)
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['ordem']
    
    def __str__(self):
        return self.titulo

class FooterInfo(models.Model):
    titulo = models.CharField(max_length=200, default="Quem Somos")
    descricao = models.TextField()
    
    link_politicas_devolucao = models.URLField(blank=True, null=True)
    link_politicas_privacidade = models.URLField(blank=True, null=True)
    link_termos_uso = models.URLField(blank=True, null=True)
    
    linkedin_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.titulo
    
    class Meta:
        verbose_name = "Informação do Footer"
        verbose_name_plural = "Informações do Footer"

class PaginaEstatica(models.Model):
    TIPO_PAGINA_CHOICES = [
        ('PRIVACIDADE', 'Política de Privacidade'),
        ('TERMOS', 'Termos de Uso'),
        ('SOBRE', 'Sobre nós'),
        ('CONTATO', 'Página de Contato'),
        ('DEVOLUCAO', 'Política de Devolução'),
    ]
    
    tipo_pagina = models.CharField(
        max_length=20, 
        choices=TIPO_PAGINA_CHOICES, 
        unique=True,
        default='PRIVACIDADE'
    )
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    data_atualizacao = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_tipo_pagina_display()} - {self.titulo}"
    
    class Meta:
        verbose_name = "Página Estática"
        verbose_name_plural = "Páginas Estáticas"
        ordering = ['tipo_pagina']


class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    imagem = models.ImageField(default='perfil_padrao.jpg', 
                               upload_to='imagens_perfil')
    
    # NOVOS CAMPOS PARA CONTROLE DE SENHA
    primeiro_login = models.BooleanField(default=True)
    tentativas_erro_senha = models.IntegerField(default=0)
    ultima_tentativa_erro = models.DateTimeField(null=True, blank=True)
    bloqueado_ate = models.DateTimeField(null=True, blank=True)
    senha_obrigatoria_alterar = models.BooleanField(default=False)  # Flag para obrigar alteração

    def __str__(self):
        return f'Perfil de {self.user.username}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Salva a imagem primeiro

        img = Image.open(self.imagem.path)  # Abre a imagem
        if img.height > 300 or img.width > 300:  # Verifica se é maior que 300x300 pixels
            output_size = (300, 300)
            img.thumbnail(output_size)  # Redimensiona a imagem
            img.save(self.imagem.path)  # Salva a imagem redimensionada

    def ultimos_pedidos(self, num=5):
        return self.user.pedidos.all().order_by("-data_pedido")[:num]
    
    # NOVOS MÉTODOS PARA CONTROLE DE TENTATIVAS
    def resetar_tentativas_erro(self):
        """Reseta o contador de tentativas de erro e remove bloqueio"""
        self.tentativas_erro_senha = 0
        self.bloqueado_ate = None
        self.senha_obrigatoria_alterar = False
        self.save()
    
    def incrementar_tentativa_erro(self):
        """Incrementa o contador de tentativas de erro"""
        self.tentativas_erro_senha += 1
        self.ultima_tentativa_erro = timezone.now()
        
        # Se atingiu 3 tentativas, marca para obrigar alteração de senha
        if self.tentativas_erro_senha >= 3:
            self.senha_obrigatoria_alterar = True
            # Bloqueia por 15 minutos
            self.bloqueado_ate = timezone.now() + timezone.timedelta(minutes=15)
        
        self.save()
    
    def esta_bloqueado(self):
        """Verifica se o usuário está bloqueado"""
        if self.bloqueado_ate:
            return self.bloqueado_ate > timezone.now()
        return False
    
    def precisa_alterar_senha(self):
        """Verifica se o usuário precisa alterar a senha"""
        return self.primeiro_login or self.senha_obrigatoria_alterar
    
    def get_tentativas_restantes(self):
        """Retorna quantas tentativas restam antes do bloqueio"""
        return max(0, 3 - self.tentativas_erro_senha)
    
    def marcar_senha_alterada(self):
        """Marca que a senha foi alterada com sucesso"""
        self.primeiro_login = False
        self.senha_obrigatoria_alterar = False
        self.resetar_tentativas_erro()
        self.save()

class ComentarioAvaliacao(models.Model):
    produto = models.ForeignKey(
        Perfume, on_delete=models.CASCADE, related_name="comentarios"
    )
    cliente = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comentarios"
    )
    comentario = models.TextField()
    avaliacao = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Avaliação {self.avaliacao} por {self.cliente.username} para {self.produto.nome}"

class EnderecoEntrega(models.Model):
    cliente = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="enderecos"
    )
    endereco = models.CharField(max_length=255)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    cep = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.endereco}, {self.cidade} - {self.estado}, CEP: {self.cep}"
    

class Pedido(models.Model):
    STATUS_CHOICES = [
        ("P", "Pendente"),
        ("PA", "Pago"),
        ("E", "Enviado"),
    ]

    cliente = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="pedidos"
    )
    endereco_entrega = models.ForeignKey(
        EnderecoEntrega, on_delete=models.PROTECT, related_name="pedidos"
    )
    data_pedido = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default="P")

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.username}"

    def total_pedido(self):
        return sum(item.quantity * item.produto.preco for item in self.itens.all())
    
    def get_status_display_name(self):
        """Retorna o nome completo do status"""
        status_dict = dict(self.STATUS_CHOICES)
        return status_dict.get(self.status, "Desconhecido")

class CartItem(models.Model):
    product = models.ForeignKey(Perfume, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.quantity} x {self.product.nome}'
    
    def subtotal(self):
        return self.product.preco * self.quantity

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Perfume, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.produto.nome}"
    
    def get_subtotal(self):
        """Retorna o subtotal do item (quantidade × preço)"""
        return self.quantity * self.preco