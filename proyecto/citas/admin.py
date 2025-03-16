from django.contrib import admin
from .models import Horario, Cita

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('medico', 'fecha', 'hora_inicio', 'hora_fin')
    list_filter = ('medico', 'fecha')
    search_fields = ('medico__usuario__first_name', 'medico__usuario__last_name')

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'medico', 'fecha', 'hora', 'estado')
    list_filter = ('estado', 'fecha', 'medico')
    search_fields = ('paciente__usuario__first_name', 'paciente__usuario__last_name', 
                     'medico__usuario__first_name', 'medico__usuario__last_name')

