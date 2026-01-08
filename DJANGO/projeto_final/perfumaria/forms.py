from django import forms
from django.core.validators import EmailValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div, ButtonHolder
from crispy_bootstrap5.bootstrap5 import FloatingField
from .models import Categoria, Perfume, Perfil, ComentarioAvaliacao, EnderecoEntrega
from django.contrib.auth.models import User




class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

class EnderecoForm(forms.ModelForm):
    class Meta:
        model = EnderecoEntrega
        fields = ['endereco', 'cidade', 'estado', 'cep']

class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['imagem']


class ContactForm(forms.Form):
    nome = forms.CharField(max_length=100)
    email = forms.CharField(validators=[EmailValidator()])
    telefone = forms.CharField(max_length=15)
    assunto = forms.CharField(max_length=100)
    mensagem = forms.CharField(widget=forms.Textarea)

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'slug', 'ordem']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-10'
        
        self.helper.layout = Layout(
            FloatingField('nome'),
            FloatingField('slug'),
            FloatingField('ordem'),
            Div(
                Submit('submit', 'Salvar', css_class='btn btn-primary me-2'),
                HTML('<a href="{% url "perfumaria:categoria_list" %}" class="btn btn-secondary">Cancelar</a>'),
                css_class='mt-3 d-flex justify-content-end'
            )
        )

class PerfumeForm(forms.ModelForm):
    class Meta:
        model = Perfume
        
        fields = ['nome', 'descricao', 'preco', 'categoria', 'imagem', 'destaque']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do perfume'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição do perfume',
                'rows': 4
            }),
            'preco': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'imagem': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'destaque': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'estoque': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Quantidade em estoque'
            }),
        }
        labels = {
            'imagem': 'Foto do Perfume',
            'destaque': 'Destacar na página inicial',
            'estoque': 'Estoque disponível'
        }
        help_texts = {
            'imagem': 'Formatos suportados: JPG, PNG, GIF. Tamanho máximo: 5MB',
            'estoque': 'Informe a quantidade de produtos disponíveis em estoque'
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'  # IMPORTANTE para upload
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-10'
        
        self.helper.layout = Layout(
            FloatingField('nome'),
            Field('descricao'),
            Row(
                Column(FloatingField('preco'), css_class='col-md-6'),
                Column(FloatingField('categoria'), css_class='col-md-6'),
            ),
            Div(
                HTML('<h5 class="mb-3"><i class="fas fa-image me-2"></i>Imagem do Produto</h5>'),
                Field('imagem', css_class='form-control-file'),
                HTML('''
                    {% if form.instance.imagem %}
                    <div class="mt-3">
                        <label class="form-label">Imagem atual:</label>
                        <div>
                            <img src="{{ form.instance.imagem.url }}" 
                                 class="img-thumbnail" 
                                 style="max-width: 200px; max-height: 200px;">
                        </div>
                    </div>
                    {% endif %}
                '''),
                css_class='mb-4 p-3 border rounded'
            ),
            Div(
                Field('destaque', css_class='form-check-input'),
                css_class='form-check form-switch mb-4'
            ),
            Div(
                Submit('submit', 'Salvar', css_class='btn btn-primary me-2'),
                HTML('<a href="{% url "perfumaria:perfume_list" %}" class="btn btn-secondary">Cancelar</a>'),
                css_class='mt-3 d-flex justify-content-end'
            )
        )

class ComentarioAvaliacaoForm(forms.ModelForm):
    AVALIACAO_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1-5

    avaliacao = forms.ChoiceField(
        choices=AVALIACAO_CHOICES,
        widget=forms.Select(attrs={'class': 'avaliacao-select form-select'})
    )

    class Meta:
        model = ComentarioAvaliacao
        fields = ['avaliacao', 'comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={
                'class': 'avaliacao-textarea form-control',
                'rows': 4,
                'placeholder': 'Escreva seu comentário aqui...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'mt-3'
        self.helper.add_input(
            Submit('submit', 'Enviar avaliação', css_class='btn btn-primary mt-3')
        )