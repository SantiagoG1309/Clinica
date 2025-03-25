from django.urls import path
from . import views

urlpatterns = [
    path('', views.generar_reportes, name='generar_reportes'),
    path('citas-diarias/', views.reporte_citas_diarias, name='reporte_citas_diarias'),
    path('medicos-solicitados/', views.reporte_medicos_solicitados, name='reporte_medicos_solicitados'),
    path('exportar-pdf/<str:tipo_reporte>/', views.exportar_pdf, name='exportar_pdf'),
    path('exportar-excel/<str:tipo_reporte>/', views.exportar_excel, name='exportar_excel'),
]

