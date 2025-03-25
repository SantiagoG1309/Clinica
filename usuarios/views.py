from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout 
from django.shortcuts import render, get_object_or_404
from .models import Medico
from django.shortcuts import render, get_object_or_404, redirect
from .models import Medico, Horario
from django.contrib import messages

from .forms import (
    LoginForm, RegistroPacienteForm, RegistroMedicoForm,
    PerfilPacienteForm, PerfilMedicoForm
)
from .models import Usuario, Paciente, Medico

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_admin():
                    return redirect('perfil_admin')
                elif user.is_medico():
                    return redirect('perfil_medico')
                else:
                    return redirect('perfil_paciente')
    else:
        form = LoginForm()
    return render(request, 'usuarios/inicio_sesion.html', {'form': form})

def registro_paciente(request):
    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, '¡Registro exitoso! Por favor, inicia sesión.')
            return redirect('login')  # Changed from 'perfil_paciente' to 'login'
    else:
        form = RegistroPacienteForm()
    return render(request, 'usuarios/registro_paciente.html', {'form': form})

@login_required
def perfil_paciente(request):
    if not request.user.is_paciente():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    if request.method == 'POST':
        form = PerfilPacienteForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil_paciente')
    else:
        form = PerfilPacienteForm(instance=request.user)
    
    return render(request, 'usuarios/perfil_paciente.html', {'form': form})
@login_required
def perfil_medico(request):
    if not request.user.is_medico():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    medico = request.user.medico  # Get the Medico instance
    
    if request.method == 'POST':
        form = PerfilMedicoForm(request.POST, request.FILES, instance=medico)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil_medico')
    else:
        form = PerfilMedicoForm(instance=medico)
    
    return render(request, 'usuarios/perfil_medico.html', {
        'form': form,
        'medico': medico
    })
    
@login_required
def perfil_admin(request):
    if not request.user.is_admin():
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')
    
    return render(request, 'usuarios/perfil_admin.html')

# Funciones para administradores
def admin_required(user):
    return user.is_authenticated and user.is_admin()

@user_passes_test(admin_required)
def gestionar_pacientes(request):
    pacientes = Paciente.objects.all()
    return render(request, 'usuarios/gestionar_pacientes.html', {'pacientes': pacientes})

@user_passes_test(admin_required)
def agregar_paciente(request):
    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paciente agregado correctamente.')
            return redirect('gestionar_pacientes')
    else:
        form = RegistroPacienteForm()
    return render(request, 'usuarios/agregar_paciente.html', {'form': form})

@user_passes_test(admin_required)
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        form = PerfilPacienteForm(request.POST, instance=paciente.usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paciente actualizado correctamente.')
            return redirect('gestionar_pacientes')
    else:
        form = PerfilPacienteForm(instance=paciente.usuario)
    return render(request, 'usuarios/editar_paciente.html', {'form': form, 'paciente': paciente})

@user_passes_test(admin_required)
def eliminar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        usuario = paciente.usuario
        paciente.delete()
        usuario.delete()
        messages.success(request, 'Paciente eliminado correctamente.')
        return redirect('gestionar_pacientes')
    return render(request, 'usuarios/eliminar_paciente.html', {'paciente': paciente})

@user_passes_test(admin_required)
def gestionar_medicos(request):
    medicos = Medico.objects.all()
    return render(request, 'usuarios/gestionar_medicos.html', {'medicos': medicos})

@user_passes_test(admin_required)
def agregar_medico(request):
    if request.method == 'POST':
        form = RegistroMedicoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Médico agregado correctamente.')
            return redirect('gestionar_medicos')
    else:
        form = RegistroMedicoForm()
    return render(request, 'usuarios/agregar_medico.html', {'form': form})

@user_passes_test(admin_required)
def editar_medico(request, pk):
    medico = get_object_or_404(Medico, pk=pk)
    if request.method == 'POST':
        form = PerfilMedicoForm(request.POST, request.FILES, instance=medico)
        if form.is_valid():
            form.save()
            messages.success(request, 'Médico actualizado correctamente.')
            return redirect('gestionar_medicos')
    else:
        form = PerfilMedicoForm(instance=medico)
    return render(request, 'usuarios/editar_medico.html', {'form': form, 'medico': medico})

@user_passes_test(admin_required)
def eliminar_medico(request, pk):
    medico = get_object_or_404(Medico, pk=pk)
    if request.method == 'POST':
        usuario = medico.usuario
        medico.delete()
        usuario.delete()
        messages.success(request, 'Médico eliminado correctamente.')
        return redirect('gestionar_medicos')
    return render(request, 'usuarios/eliminar_medico.html', {'medico': medico})



@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('home')


def detalle_medico(request, medico_id):
    medico = get_object_or_404(Medico, id=medico_id)
    return render(request, 'detalle_medico.html', {'medico': medico})



def agendar_cita(request, medico_id, horario_id):
    medico = get_object_or_404(Medico, id=medico_id)
    horario = get_object_or_404(Horario, id=horario_id, medico=medico)
    
    if request.method == "POST":
        if horario.disponible:
            horario.disponible = False
            horario.save()
            messages.success(request, "Cita agendada con éxito.")
            return redirect('detalle_medico', medico_id=medico_id)
        else:
            messages.error(request, "Este horario ya no está disponible.")
    
    return render(request, 'agendar_cita.html', {'medico': medico, 'horario': horario})