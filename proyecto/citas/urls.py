from django.urls import path
from . import views

urlpatterns = [
    # Vistas para pacientes
    path('explorar-medicos/', views.explorar_medicos, name='explorar_medicos'),
    path('reservar-cita/<int:medico_id>/<str:fecha>/', views.reservar_cita, name='reservar_cita'),
    path('mis-citas/', views.historial_citas, name='historial_citas'),
    path('cancelar-cita/<int:cita_id>/', views.cancelar_cita, name='cancelar_cita'),
    
    # Vistas para médicos
    path('mis-horarios/', views.mis_horarios, name='mis_horarios'),
    path('agregar-horario/', views.agregar_horario, name='agregar_horario'),
    path('editar-horario/<int:horario_id>/', views.editar_horario, name='editar_horario'),
    path('eliminar-horario/<int:horario_id>/', views.eliminar_horario, name='eliminar_horario'),
    path('citas-asignadas/', views.citas_asignadas, name='citas_asignadas'),
    path('completar-cita/<int:cita_id>/', views.completar_cita, name='completar_cita'),
    path('marcar-no-asistio/<int:cita_id>/', views.marcar_no_asistio, name='marcar_no_asistio'),
    path('perfil/<int:id>/', views.perfil_medico, name='perfil_medico'),
]