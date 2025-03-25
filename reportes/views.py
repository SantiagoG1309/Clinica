from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count
from django.utils import timezone
from citas.models import Cita
from usuarios.models import Medico
import datetime
import csv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

def admin_required(user):
    return user.is_authenticated and user.is_admin()

@user_passes_test(admin_required)
def generar_reportes(request):
    return render(request, 'reportes/generar_reportes.html')

@user_passes_test(admin_required)
def reporte_citas_diarias(request):
    fecha = request.GET.get('fecha', timezone.now().date())
    if isinstance(fecha, str):
        try:
            fecha = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()
        except ValueError:
            fecha = timezone.now().date()
    
    citas = Cita.objects.filter(fecha=fecha)
    
    if not citas.exists():
        messages.warning(request, f"No hay citas registradas para la fecha {fecha.strftime('%d/%m/%Y')}.")
    
    return render(request, 'reportes/reporte_citas_diarias.html', {
        'citas': citas,
        'fecha': fecha,
        'tipo_reporte': 'citas-diarias'
    })

@user_passes_test(admin_required)
def reporte_medicos_solicitados(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio and fecha_fin:
        try:
            fecha_inicio = datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Formato de fecha inválido.')
            return redirect('generar_reportes')
    else:
        # Por defecto, mostrar el mes actual
        hoy = timezone.now().date()
        fecha_inicio = datetime.date(hoy.year, hoy.month, 1)
        fecha_fin = hoy
    
    # Obtener médicos con más citas en el período seleccionado
    medicos_solicitados = Medico.objects.filter(
        citas__fecha__gte=fecha_inicio,
        citas__fecha__lte=fecha_fin
    ).annotate(
        total_citas=Count('citas')
    ).order_by('-total_citas')
    
    if not medicos_solicitados.exists():
        messages.warning(request, f"No hay médicos con citas en el período seleccionado ({fecha_inicio.strftime('%d/%m/%Y')} a {fecha_fin.strftime('%d/%m/%Y')}).")
    
    return render(request, 'reportes/reporte_medicos_solicitados.html', {
        'medicos_solicitados': medicos_solicitados,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'tipo_reporte': 'medicos-solicitados'
    })

@user_passes_test(admin_required)
def exportar_pdf(request, tipo_reporte):
    # Crear un buffer para el PDF
    buffer = io.BytesIO()
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    if tipo_reporte == 'citas-diarias':
        fecha = request.GET.get('fecha', timezone.now().date())
        if isinstance(fecha, str):
            try:
                fecha = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                fecha = timezone.now().date()
        
        citas = Cita.objects.filter(fecha=fecha)
        
        # Crear tabla para el PDF
        data = [['Paciente', 'Médico', 'Hora', 'Estado']]
        for cita in citas:
            data.append([
                str(cita.paciente),
                str(cita.medico),
                cita.hora.strftime('%H:%M'),
                cita.get_estado_display()
            ])
        
        title = f"Reporte de Citas Diarias - {fecha}"
    
    elif tipo_reporte == 'medicos-solicitados':
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            try:
                fecha_inicio = datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                fecha_fin = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio = datetime.date(timezone.now().year, timezone.now().month, 1)
                fecha_fin = timezone.now().date()
        else:
            hoy = timezone.now().date()
            fecha_inicio = datetime.date(hoy.year, hoy.month, 1)
            fecha_fin = hoy
        
        medicos_solicitados = Medico.objects.filter(
            citas__fecha__gte=fecha_inicio,
            citas__fecha__lte=fecha_fin
        ).annotate(
            total_citas=Count('citas')
        ).order_by('-total_citas')
        
        # Crear tabla para el PDF
        data = [['Médico', 'Especialidades', 'Total Citas']]
        for medico in medicos_solicitados:
            especialidades = ", ".join([e.nombre for e in medico.especialidades.all()])
            data.append([
                str(medico),
                especialidades,
                medico.total_citas
            ])
        
        title = f"Reporte de Médicos Más Solicitados - {fecha_inicio} a {fecha_fin}"
    
    else:
        return HttpResponse("Tipo de reporte no válido", status=400)
    
    # Crear la tabla y aplicar estilos
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Construir el PDF
    doc.title = title
    doc.build(elements)
    
    # Obtener el valor del buffer y crear la respuesta HTTP
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{tipo_reporte}.pdf"'
    response.write(pdf)
    
    return response

@user_passes_test(admin_required)
def exportar_excel(request, tipo_reporte):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{tipo_reporte}.csv"'
    
    writer = csv.writer(response)
    
    if tipo_reporte == 'citas-diarias':
        fecha = request.GET.get('fecha', timezone.now().date())
        if isinstance(fecha, str):
            try:
                fecha = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                fecha = timezone.now().date()
        
        citas = Cita.objects.filter(fecha=fecha)
        
        # Escribir encabezados
        writer.writerow(['Paciente', 'Médico', 'Hora', 'Estado'])
        
        # Escribir datos
        for cita in citas:
            writer.writerow([
                str(cita.paciente),
                str(cita.medico),
                cita.hora.strftime('%H:%M'),
                cita.get_estado_display()
            ])
    
    elif tipo_reporte == 'medicos-solicitados':
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            try:
                fecha_inicio = datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                fecha_fin = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio = datetime.date(timezone.now().year, timezone.now().month, 1)
                fecha_fin = timezone.now().date()
        else:
            hoy = timezone.now().date()
            fecha_inicio = datetime.date(hoy.year, hoy.month, 1)
            fecha_fin = hoy
        
        medicos_solicitados = Medico.objects.filter(
            citas__fecha__gte=fecha_inicio,
            citas__fecha__lte=fecha_fin
        ).annotate(
            total_citas=Count('citas')
        ).order_by('-total_citas')
        
        # Escribir encabezados
        writer.writerow(['Médico', 'Especialidades', 'Total Citas'])
        
        # Escribir datos
        for medico in medicos_solicitados:
            especialidades = ", ".join([e.nombre for e in medico.especialidades.all()])
            writer.writerow([
                str(medico),
                especialidades,
                medico.total_citas
            ])
    
    else:
        return HttpResponse("Tipo de reporte no válido", status=400)
    
    return response

