from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import Horario, Cita
from .forms import HorarioForm, BuscarMedicoForm, ReservarCitaForm, CancelarCitaForm
from usuarios.models import Medico, Paciente
import datetime
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Cita
from .emails import enviar_recordatorio_correo  # Importar la función de correo

@login_required
def explorar_medicos(request):
    if not request.user.is_paciente():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    form = BuscarMedicoForm(request.GET or None)
    medicos = Medico.objects.all().prefetch_related('especialidades', 'usuario')
    fecha_actual = timezone.now().date()
    
    if form.is_valid():
        especialidad = form.cleaned_data.get('especialidad')
        fecha = form.cleaned_data.get('fecha')
        
        if especialidad:
            medicos = medicos.filter(especialidades=especialidad)
        
        if fecha:
            if fecha < fecha_actual:
                messages.warning(request, 'La fecha seleccionada no puede ser anterior a hoy.')
                fecha = fecha_actual
            
            # Filtrar médicos con horarios disponibles
            medicos_disponibles = []
            for medico in medicos:
                horarios = Horario.objects.filter(
                    medico=medico, 
                    fecha=fecha
                ).order_by('hora_inicio')
                
                if horarios.exists():
                    for horario in horarios:
                        # Verificar disponibilidad en intervalos de 30 minutos
                        hora_actual = horario.hora_inicio
                        while hora_actual < horario.hora_fin:
                            cita_existe = Cita.objects.filter(
                                medico=medico,
                                fecha=fecha,
                                hora=hora_actual,
                                estado__in=[Cita.PENDIENTE, Cita.COMPLETADA]  # Solo 'pendiente' y 'completada'
                            ).exists()
                            
                            if not cita_existe:
                                medicos_disponibles.append(medico)
                                break
                            
                            hora_actual = (datetime.datetime.combine(fecha_actual, hora_actual) + 
                                         datetime.timedelta(minutes=30)).time()
                        
                        if medico in medicos_disponibles:
                            break
            
            medicos = medicos_disponibles
    
    return render(request, 'citas/explorar_medicos.html', {
        'form': form,
        'medicos': list(set(medicos)),  # Eliminar duplicados
        'fecha_seleccionada': form.cleaned_data.get('fecha') if form.is_valid() else None,
        'fecha_actual': fecha_actual
    })
    
@login_required
def reservar_cita(request, medico_id, fecha):
    if not request.user.is_paciente():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    medico = get_object_or_404(Medico, id=medico_id)
    fecha_obj = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()
    
    horarios = Horario.objects.filter(medico=medico, fecha=fecha_obj)
    
    if not horarios.exists():
        messages.error(request, 'No hay horarios disponibles para este médico en la fecha seleccionada.')
        return redirect('explorar_medicos')
    
    horarios_disponibles = []
    for horario in horarios:
        hora_actual = horario.hora_inicio
        while hora_actual < horario.hora_fin:
            cita_existe = Cita.objects.filter(
                medico=medico, 
                fecha=fecha_obj, 
                hora=hora_actual,
                estado__in=[Cita.PENDIENTE, Cita.COMPLETADA]  # Solo citas activas
            ).exists()
            
            if not cita_existe:
                horarios_disponibles.append({
                    'hora': hora_actual,
                    'horario': horario
                })
            
            hora_actual = (datetime.datetime.combine(datetime.date.today(), hora_actual) + 
                          datetime.timedelta(minutes=30)).time()
    
    if not horarios_disponibles:
        messages.error(request, 'No hay horas disponibles para este médico en la fecha seleccionada.')
        return redirect('explorar_medicos')
    
    if request.method == 'POST':
        form = ReservarCitaForm(request.POST, horarios_disponibles=horarios_disponibles)
        if form.is_valid():
            try:
                cita = form.save(commit=False)
                cita.paciente = request.user.paciente
                cita.medico = medico
                cita.fecha = fecha_obj
                cita.estado = Cita.PENDIENTE  # 'pendiente'
                
                # Verificación manual de unicidad para citas activas
                if Cita.objects.filter(
                    medico=cita.medico,
                    fecha=cita.fecha,
                    hora=cita.hora,
                    estado__in=[Cita.PENDIENTE, Cita.COMPLETADA]
                ).exists():
                    messages.error(request, 'Ya existe una cita activa en este horario.')
                    return render(request, 'citas/reservar_cita.html', {
                        'form': form,
                        'medico': medico,
                        'fecha': fecha_obj,
                        'horarios_disponibles': horarios_disponibles
                    })
                
                cita.save()

                # Enviar el recordatorio por correo
                enviar_recordatorio_correo(cita)

                messages.success(request, 'Cita reservada correctamente. Se ha enviado un correo de confirmación.')
                return redirect('historial_citas')
            except Exception as e:
                messages.error(request, 'Error al guardar la cita. Por favor, intente nuevamente.')
                print(f"Error saving appointment: {str(e)}")
    else:
        initial_data = {
            'medico': medico,
            'fecha': fecha_obj,
        }
        form = ReservarCitaForm(initial=initial_data, horarios_disponibles=horarios_disponibles)
    
    return render(request, 'citas/reservar_cita.html', {
        'form': form,
        'medico': medico,
        'fecha': fecha_obj,
        'horarios_disponibles': horarios_disponibles
    })

@login_required
def historial_citas(request):
    if not request.user.is_paciente():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')

    now = timezone.now()
    
    citas = Cita.objects.filter(
        paciente=request.user.paciente
    ).select_related(
        'medico',
        'medico__usuario'
    ).prefetch_related(
        'medico__especialidades'
    )
    
    citas_proximas = citas.filter(
        Q(fecha__gt=now.date()) | 
        Q(fecha=now.date(), hora__gt=now.time()),
        estado=Cita.PENDIENTE  # 'pendiente'
    ).order_by('fecha', 'hora')
    
    citas_pasadas = citas.filter(
        Q(fecha__lt=now.date()) |
        Q(fecha=now.date(), hora__lt=now.time()),
        estado=Cita.COMPLETADA  # 'completada'
    ).order_by('-fecha', '-hora')
    
    citas_canceladas = citas.filter(
        estado=Cita.CANCELADA  # 'cancelada'
    ).order_by('-fecha', '-hora')
    
    context = {
        'citas_proximas': citas_proximas,
        'citas_pasadas': citas_pasadas,
        'citas_canceladas': citas_canceladas,
    }
    
    return render(request, 'citas/historial_citas.html', context)

@login_required
def cancelar_cita(request, cita_id):
    if not request.user.is_paciente():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    cita = get_object_or_404(Cita, id=cita_id, paciente=request.user.paciente)
    
    # Verificar que la cita no sea en el pasado
    if cita.is_past():
        messages.error(request, 'No puedes cancelar una cita que ya ha pasado.')
        return redirect('historial_citas')
    
    if request.method == 'POST':
        form = CancelarCitaForm(request.POST)
        if form.is_valid():
            cita.estado = Cita.CANCELADA  # 'cancelada'
            cita.save()
            messages.success(request, 'Cita cancelada correctamente. El horario ahora está disponible.')
            return redirect('historial_citas')
    else:
        form = CancelarCitaForm()
    
    return render(request, 'citas/cancelar_cita.html', {'form': form, 'cita': cita})


# Vistas para médicos

@login_required
def citas_asignadas(request):
    if not request.user.is_medico():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    now = timezone.now()
    today = now.date()
    
    # Obtener todas las citas del médico logueado
    citas = Cita.objects.filter(
        medico=request.user.medico
    ).select_related(
        'paciente',
        'paciente__usuario'
    ).order_by('fecha', 'hora')
    
    # Filtrar citas para las pestañas
    citas_hoy = citas.filter(fecha=today, estado='PENDIENTE')  # Citas pendientes para hoy
    citas_proximas = citas.filter(fecha__gt=today, estado='PENDIENTE')  # Citas pendientes futuras
    citas_pasadas = citas.filter(Q(fecha__lt=today) | Q(estado__in=['COMPLETADA', 'NO_ASISTIO', 'CANCELADA']))  # Citas pasadas o completadas
    
    context = {
        'citas_hoy': citas_hoy,
        'citas_proximas': citas_proximas,
        'citas_pasadas': citas_pasadas,
        'today': today,
    }
    
    return render(request, 'citas/citas_asignadas.html', context)

@login_required
def completar_cita(request, cita_id):
    if not request.user.is_medico():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    cita = get_object_or_404(Cita, id=cita_id, medico=request.user.medico)
    
    if cita.estado == 'CANCELADA':
        messages.error(request, 'No puedes completar una cita que ha sido cancelada.')
        return redirect('citas_asignadas')
    
    cita.estado = 'COMPLETADA'
    cita.save()
    messages.success(request, 'Cita marcada como completada.')
    
    return redirect('citas_asignadas')


@login_required
def mis_horarios(request):
    if not request.user.is_medico():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    horarios = Horario.objects.filter(medico=request.user.medico)
    
    return render(request, 'citas/mis_horarios.html', {'horarios' : horarios})

@login_required
def agregar_horario(request):
    if not request.user.is_medico():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    medico = getattr(request.user, 'medico', None)  # Obtiene el perfil del médico si existe
    
    if request.method == 'POST':
        form = HorarioForm(request.POST)
        if form.is_valid():
            horario = form.save(commit=False)
            horario.medico = medico
            horario.save()
            messages.success(request, 'Horario agregado correctamente.')
            return redirect('mis_horarios')
    else:
        form = HorarioForm()
    
    return render(request, 'citas/agregar_horario.html', {'form': form, 'medico': medico})

@login_required
def editar_horario(request, horario_id):
    if not request.user.is_medico():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    horario = get_object_or_404(Horario, id=horario_id, medico=request.user.medico)
    
    if request.method == 'POST':
        form = HorarioForm(request.POST, instance=horario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Horario actualizado correctamente.')
            return redirect('mis_horarios')
    else:
        form = HorarioForm(instance=horario)
    
    return render(request, 'citas/editar_horario.html', {'form': form, 'horario': horario})

@login_required
def eliminar_horario(request, horario_id):
    if not request.user.is_medico():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    horario = get_object_or_404(Horario, id=horario_id, medico=request.user.medico)
    
    # Verificar que no haya citas asociadas a este horario
    citas = Cita.objects.filter(
        medico=request.user.medico,
        fecha=horario.fecha,
        hora__gte=horario.hora_inicio,
        hora__lt=horario.hora_fin
    )
    
    if citas.exists():
        messages.error(request, 'No puedes eliminar este horario porque hay citas programadas.')
        return redirect('mis_horarios')
    
    if request.method == 'POST':
        horario.delete()
        messages.success(request, 'Horario eliminado correctamente.')
        return redirect('mis_horarios')
    
    return render(request, 'citas/eliminar_horario.html', {'horario': horario})

@login_required
def citas_asignadas(request):
    if not request.user.is_medico():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    citas = Cita.objects.filter(medico=request.user.medico)
    
    return render(request, 'citas/citas_asignadas.html', {'citas': citas})

@login_required
def completar_cita(request, cita_id):
    if not request.user.is_medico():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    cita = get_object_or_404(Cita, id=cita_id, medico=request.user.medico)
    
    # Verificar que la cita no esté cancelada
    if cita.estado == Cita.CANCELADA:
        messages.error(request, 'No puedes completar una cita que ha sido cancelada.')
        return redirect('citas_asignadas')
    
    cita.estado = Cita.COMPLETADA
    cita.save()
    messages.success(request, 'Cita marcada como completada.')
    
    return redirect('citas_asignadas')

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Medico
from .forms import PerfilMedicoForm  # Asegúrate de importar el formulario

@login_required
def perfil_medico(request, id):
    medico = get_object_or_404(Medico, id=id)

    try:
        usuario_medico = request.user.medico
        if usuario_medico.id != medico.id:
            messages.error(request, 'No tienes permiso para acceder a este perfil.')
            return redirect('home')
    except Medico.DoesNotExist:
        messages.error(request, 'No tienes un perfil de médico asociado.')
        return redirect('home')

    if request.method == 'POST':
        form = PerfilMedicoForm(request.POST, request.FILES, instance=medico)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil_medico', id=medico.id)
    else:
        form = PerfilMedicoForm(instance=medico)

    # Depuración: Imprimir los datos del médico para verificar
    print(f"Medico: {medico}, Biografía: {medico.biografia}, Dirección: {medico.direccion}, Experiencia: {medico.experiencia}")

    return render(request, 'usuarios/perfil_medico.html', {
        'form': form,
        'medico': medico
    })
    
    
@login_required
def marcar_no_asistio(request, cita_id):
    if not request.user.is_medico():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    cita = get_object_or_404(Cita, id=cita_id, medico=request.user.medico)
    
    if cita.estado == 'CANCELADA':
        messages.error(request, 'No puedes marcar como no asistió una cita cancelada.')
        return redirect('citas_asignadas')
    
    cita.estado = 'NO_ASISTIO'
    cita.save()
    messages.success(request, 'Cita marcada como no asistió.')
    
    return redirect('citas_asignadas')