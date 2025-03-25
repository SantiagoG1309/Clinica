from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Paciente, Medico, Especialidad

class PacienteInline(admin.StackedInline):
    model = Paciente
    can_delete = False

class MedicoInline(admin.StackedInline):
    model = Medico
    can_delete = False

class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'is_staff')
    list_filter = ('tipo_usuario', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('tipo_usuario', 'telefono')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('tipo_usuario', 'telefono')}),
    )
    
    def get_inlines(self, request, obj=None):
        if obj:
            if obj.tipo_usuario == Usuario.PACIENTE:
                return [PacienteInline]
            elif obj.tipo_usuario == Usuario.MEDICO:
                return [MedicoInline]
        return []

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Paciente)
admin.site.register(Medico)
admin.site.register(Especialidad)

