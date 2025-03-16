from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario, Paciente, Medico, Especialidad

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))

class RegistroPacienteForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')
    email = forms.EmailField(max_length=254, required=True, label='Correo electrónico')
    telefono = forms.CharField(max_length=15, required=True, label='Teléfono')
    documento_identidad = forms.CharField(max_length=20, required=True, label='Documento de identidad')
    edad = forms.IntegerField(min_value=0, required=True, label='Edad')
    
    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo_usuario = Usuario.PACIENTE
        if commit:
            user.save()
            Paciente.objects.create(
                usuario=user,
                documento_identidad=self.cleaned_data['documento_identidad'],
                edad=self.cleaned_data['edad']
            )
        return user

class RegistroMedicoForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')
    email = forms.EmailField(max_length=254, required=True, label='Correo electrónico')
    telefono = forms.CharField(max_length=15, required=True, label='Teléfono')
    especialidades = forms.ModelMultipleChoiceField(
        queryset=Especialidad.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Especialidades'
    )
    
    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo_usuario = Usuario.MEDICO
        if commit:
            user.save()
            medico = Medico.objects.create(usuario=user)
            medico.especialidades.set(self.cleaned_data.get('especialidades'))
        return user

class PerfilPacienteForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')
    email = forms.EmailField(max_length=254, required=True, label='Correo electrónico')
    telefono = forms.CharField(max_length=15, required=True, label='Teléfono')
    documento_identidad = forms.CharField(max_length=20, required=True, label='Documento de identidad')
    edad = forms.IntegerField(min_value=0, required=True, label='Edad')
    
    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'email', 'telefono')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.instance, 'paciente'):
            self.fields['documento_identidad'].initial = self.instance.paciente.documento_identidad
            self.fields['edad'].initial = self.instance.paciente.edad
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            if hasattr(user, 'paciente'):
                user.paciente.documento_identidad = self.cleaned_data.get('documento_identidad')
                user.paciente.edad = self.cleaned_data.get('edad')
                user.paciente.save()
        return user

class PerfilMedicoForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        max_length=254, 
        required=True, 
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    telefono = forms.CharField(
        max_length=15, 
        required=True, 
        label='Teléfono',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Medico
        fields = ['biografia', 'direccion', 'experiencia', 'especialidades']
        widgets = {
            'biografia': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'experiencia': forms.NumberInput(attrs={'class': 'form-control'}),
            'especialidades': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.usuario.first_name
            self.fields['last_name'].initial = self.instance.usuario.last_name
            self.fields['email'].initial = self.instance.usuario.email
            self.fields['telefono'].initial = self.instance.usuario.telefono

    def save(self, commit=True):
        medico = super().save(commit=False)
        if commit:
            medico.save()
            usuario = medico.usuario
            usuario.first_name = self.cleaned_data['first_name']
            usuario.last_name = self.cleaned_data['last_name']
            usuario.email = self.cleaned_data['email']
            usuario.telefono = self.cleaned_data['telefono']
            usuario.save()
            self.save_m2m()
        return medico