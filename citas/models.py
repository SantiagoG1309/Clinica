from django.db import models
from usuarios.models import Paciente, Medico
from django.utils import timezone

class Horario(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='horarios')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    def __str__(self):
        return f"{self.medico} - {self.fecha} ({self.hora_inicio} - {self.hora_fin})"
    
    class Meta:
        unique_together = ('medico', 'fecha', 'hora_inicio')
        ordering = ['fecha', 'hora_inicio']

class Cita(models.Model):
    PENDIENTE = 'pendiente'
    COMPLETADA = 'completada'
    CANCELADA = 'cancelada'
    
    ESTADO_CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (COMPLETADA, 'Completada'),
        (CANCELADA, 'Cancelada'),
    ]
    
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='citas')
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=PENDIENTE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.paciente} con {self.medico} - {self.fecha} {self.hora}"
    
    class Meta:
        # Eliminamos unique_together para permitir múltiples citas en el mismo horario
        ordering = ['fecha', 'hora']
    
    def is_past(self):
        now = timezone.now()
        cita_datetime = timezone.make_aware(
            timezone.datetime.combine(self.fecha, self.hora)
        )
        return cita_datetime < now