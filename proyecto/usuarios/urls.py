from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='usuarios/recuperar_contrasena.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Registro
    path('registro/paciente/', views.registro_paciente, name='registro_paciente'),
    
    # Perfiles
    path('perfil/paciente/', views.perfil_paciente, name='perfil_paciente'),
    path('perfil/medico/', views.perfil_medico, name='perfil_medico'),
    path('perfil/admin/', views.perfil_admin, name='perfil_admin'),
    
    # Administración
    path('admin/pacientes/', views.gestionar_pacientes, name='gestionar_pacientes'),
    path('admin/pacientes/agregar/', views.agregar_paciente, name='agregar_paciente'),
    path('admin/pacientes/editar/<int:pk>/', views.editar_paciente, name='editar_paciente'),
    path('admin/pacientes/eliminar/<int:pk>/', views.eliminar_paciente, name='eliminar_paciente'),
    
    path('admin/medicos/', views.gestionar_medicos, name='gestionar_medicos'),
    path('admin/medicos/agregar/', views.agregar_medico, name='agregar_medico'),
    path('admin/medicos/editar/<int:pk>/', views.editar_medico, name='editar_medico'),
    path('admin/medicos/eliminar/<int:pk>/', views.eliminar_medico, name='eliminar_medico'),
    
    path('medico/<int:medico_id>/', views.detalle_medico, name='detalle_medico'),
    path('agendar_cita/<int:medico_id>/<int:horario_id>/', views.agendar_cita, name='agendar_cita'),

]

