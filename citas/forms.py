from django import forms
from .models import Horario, Cita
from usuarios.models import Medico, Especialidad
from django.utils import timezone
import datetime

class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['fecha', 'hora_inicio', 'hora_fin']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        
        if fecha and hora_inicio and hora_fin:
            # Verificar que la fecha no sea en el pasado
            if fecha < timezone.now().date():
                raise forms.ValidationError("No puedes crear horarios para fechas pasadas.")
            
            # Verificar que la hora de fin sea posterior a la hora de inicio
            if hora_fin <= hora_inicio:
                raise forms.ValidationError("La hora de fin debe ser posterior a la hora de inicio.")
        
        return cleaned_data
class BuscarMedicoForm(forms.Form):
    especialidad = forms.ModelChoiceField(
        queryset=Especialidad.objects.all(),
        required=False,
        empty_label="Todas las especialidades",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Seleccione una especialidad'
        })
    )
    fecha = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': timezone.now().date().isoformat()
        })
    )
    
    
class ReservarCitaForm(forms.ModelForm):
    medico = forms.ModelChoiceField(
        queryset=Medico.objects.all(),
        widget=forms.HiddenInput()
    )
    fecha = forms.DateField(
        widget=forms.HiddenInput()
    )
    hora = forms.TimeField(
        widget=forms.Select(attrs={
            'class': 'form-control',
            'aria-label': 'Seleccione una hora disponible'
        }),
        required=True,
        label="Hora disponible"
    )
    
    class Meta:
        model = Cita
        fields = ['medico', 'fecha', 'hora']

    def __init__(self, *args, **kwargs):
        horarios_disponibles = kwargs.pop('horarios_disponibles', None)
        super().__init__(*args, **kwargs)
        
        if horarios_disponibles:
            opciones_hora = []
            horas_usadas = set()
            
            for horario_info in horarios_disponibles:
                hora_actual = horario_info['horario'].hora_inicio
                while hora_actual < horario_info['horario'].hora_fin:
                    hora_str = hora_actual.strftime('%H:%M')
                    
                    if hora_str not in horas_usadas:
                        hora_display = datetime.datetime.strptime(hora_str, '%H:%M').strftime('%I:%M %p')
                        opciones_hora.append((hora_str, hora_display))
                        horas_usadas.add(hora_str)
                    
                    hora_actual = (datetime.datetime.combine(datetime.date.today(), hora_actual) + 
                                 datetime.timedelta(minutes=30)).time()
            
            if opciones_hora:
                self.fields['hora'].widget = forms.Select(
                    attrs={
                        'class': 'form-control',
                        'aria-label': 'Seleccione una hora disponible'
                    },
                    choices=[('', 'Seleccione una hora')] + sorted(opciones_hora)
                )
            else:
                self.fields['hora'].widget = forms.Select(
                    attrs={
                        'class': 'form-control is-invalid',
                        'disabled': 'disabled'
                    },
                    choices=[('', 'No hay horarios disponibles')]
                )
                
class CancelarCitaForm(forms.Form):
    confirmar = forms.BooleanField(
        required=True,
        label="Confirmo que deseo cancelar esta cita",
        help_text="Esta acción no se puede deshacer."
    )


class PerfilMedicoForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = ['biografia', 'direccion', 'experiencia', 'especialidades']
        widgets = {
            'biografia': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'experiencia': forms.NumberInput(attrs={'class': 'form-control'}),
            'especialidades': forms.CheckboxSelectMultiple(),  # Para múltiples especialidades
        }
        labels = {
            'biografia': 'Biografía',
            'direccion': 'Dirección',
            'experiencia': 'Años de experiencia',
            'especialidades': 'Especialidades',
        }