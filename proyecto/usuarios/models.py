from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class Usuario(AbstractUser):
    ADMIN = 'admin'
    MEDICO = 'medico'
    PACIENTE = 'paciente'
    
    TIPO_USUARIO_CHOICES = [
        (ADMIN, 'Administrador'),
        (MEDICO, 'Médico'),
        (PACIENTE, 'Paciente'),
    ]
    
    tipo_usuario = models.CharField(
        max_length=10,
        choices=TIPO_USUARIO_CHOICES,
        default=PACIENTE,
    )
    telefono = models.CharField(max_length=15, blank=True, null=True)
    foto = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)  # Nuevo campo
    
    def __str__(self):
        return self.username
    
    def is_admin(self):
        return self.tipo_usuario == self.ADMIN
    
    def is_medico(self):
        return self.tipo_usuario == self.MEDICO
    
    def is_paciente(self):
        return self.tipo_usuario == self.PACIENTE

class Paciente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='paciente')
    documento_identidad = models.CharField(max_length=10, unique=True)
    edad = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.documento_identidad}"

class Especialidad(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Especialidades"

class Medico(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='medico')
    especialidades = models.ManyToManyField('Especialidad', related_name='medicos')
    biografia = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    experiencia = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Dr. {self.usuario.get_full_name()}"
    
    @property
    def especialidad(self):
        return ", ".join([esp.nombre for esp in self.especialidades.all()]) if self.especialidades.exists() else "No especificada"
    class Meta:
        verbose_name = "Médico"
        verbose_name_plural = "Médicos"



class Horario(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='horarios_citas')
    fecha = models.DateField()
    hora = models.TimeField()
    disponible = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.medico} - {self.fecha} {self.hora}"
    
    class Meta:
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"
        unique_together = ('medico', 'fecha', 'hora')