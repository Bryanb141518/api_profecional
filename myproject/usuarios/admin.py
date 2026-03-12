from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Usuario, PerfilUniversitario, PerfilSecundaria,
    Semestre, Materia, Nota, Tarea, ClaseHorario
)

# USUARIO

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    # Columnas en la lista
    list_display  = ('email', 'nombre', 'apellido', 'tipo_estudiante',
                     'is_active', 'estado_bloqueo', 'intentos_fallidos')
    list_filter   = ('is_active', 'is_staff', 'tipo_estudiante', 'genero')
    search_fields = ('email', 'nombre', 'apellido')
    ordering      = ('email',)

    # Acciones personalizadas
    actions = ['desbloquear_usuarios', 'desactivar_usuarios', 'activar_usuarios']

    # Campos al ver/editar un usuario
    fieldsets = (
        ('Identificación', {
            'fields': ('email', 'password')
        }),
        ('Información personal', {
            'fields': ('nombre', 'apellido', 'edad', 'genero')
        }),
        ('Tipo de estudiante', {
            'fields': ('tipo_estudiante',)
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Seguridad', {
            'fields': ('intentos_fallidos', 'bloqueado_hasta'),
            'classes': ('collapse',),
        }),
    )

    # Campos al crear un usuario nuevo desde el admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'apellido', 'edad',
                       'genero', 'tipo_estudiante', 'password1', 'password2'),
        }),
    )

    def estado_bloqueo(self, obj):
        if obj.bloqueado_hasta and obj.bloqueado_hasta > timezone.now():
            return format_html(
                '<span style="color:red;font-weight:bold"> Bloqueado hasta {}</span>',
                obj.bloqueado_hasta.strftime('%d/%m/%Y %H:%M')
            )
        return format_html('<span style="color:green"> Activo</span>')

    estado_bloqueo.short_description = 'Estado'

    @admin.action(description='Desbloquear usuarios seleccionados')
    def desbloquear_usuarios(self, request, queryset):
        queryset.update(intentos_fallidos=0, bloqueado_hasta=None)
        self.message_user(request, f'{queryset.count()} usuario(s) desbloqueado(s).')

    @admin.action(description='Desactivar usuarios seleccionados')
    def desactivar_usuarios(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} usuario(s) desactivado(s).')

    @admin.action(description='Activar usuarios seleccionados')
    def activar_usuarios(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} usuario(s) activado(s).')


# PERFIL UNIVERSITARIO

class SemestreInline(admin.TabularInline):
    model       = Semestre
    extra       = 0
    fields      = ('numero', 'estado')
    show_change_link = True


@admin.register(PerfilUniversitario)
class PerfilUniversitarioAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'universidad', 'carrera', 'semestre_actual',
                     'creditos_aprobados', 'creditos_para_graduarse', 'progreso_carrera')
    list_filter   = ('universidad', 'carrera', 'escala_notas')
    search_fields = ('usuario__email', 'usuario__nombre', 'universidad', 'carrera')
    readonly_fields = ('creditos_faltantes', 'semestres_minimos')
    inlines       = [SemestreInline]

    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Institución', {
            'fields': ('universidad', 'carrera', 'facultad', 'modalidad')
        }),
        ('Créditos', {
            'fields': (
                'creditos_para_graduarse', 'creditos_aprobados',
                'creditos_faltantes',
                'creditos_minimos_por_semestre', 'creditos_maximos_por_semestre',
            )
        }),
        ('Semestres', {
            'fields': ('semestre_actual', 'total_semestres', 'anno_ingreso', 'semestres_minimos')
        }),
        ('Notas', {
            'fields': ('escala_notas', 'nota_minima_global', 'promedio_minimo_carrera')
        }),
    )

    def progreso_carrera(self, obj):
        if obj.creditos_para_graduarse > 0:
            pct = (obj.creditos_aprobados / obj.creditos_para_graduarse) * 100
            color = '#22c55e' if pct >= 75 else '#f59e0b' if pct >= 40 else '#ef4444'
            return format_html(
                '<div style="width:100px;background:#e5e7eb;border-radius:4px">'
                '<div style="width:{}%;background:{};height:14px;border-radius:4px"></div>'
                '</div> <span style="font-size:11px">{:.1f}%</span>',
                min(pct, 100), color, pct
            )
        return '—'

    progreso_carrera.short_description = 'Progreso'
# PERFIL SECUNDARIA


@admin.register(PerfilSecundaria)
class PerfilSecundariaAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'nombre_instituto', 'curso_actual',
                     'periodo_actual', 'total_de_periodos')
    search_fields = ('usuario__email', 'nombre_instituto', 'curso_actual')
    list_filter   = ('nombre_instituto',)


# ══════════════════════════════════════════
# SEMESTRE
# ══════════════════════════════════════════

class MateriaInline(admin.TabularInline):
    model  = Materia
    extra  = 0
    fields = ('nombre', 'creditos', 'escala_notas', 'nota_minima_aprobacion',
              'estado', 'color')
    show_change_link = True


@admin.register(Semestre)
class SemestreAdmin(admin.ModelAdmin):
    list_display  = ('__str__', 'perfil', 'numero', 'estado',
                     'total_materias', 'creditos_semestre')
    list_filter   = ('estado',)
    search_fields = ('perfil__usuario__email', 'perfil__carrera')
    inlines       = [MateriaInline]

    def total_materias(self, obj):
        return obj.materias.count()
    total_materias.short_description = 'Materias'

    def creditos_semestre(self, obj):
        return sum(m.creditos for m in obj.materias.all())
    creditos_semestre.short_description = 'Créditos'

# MATERIA


class NotaInline(admin.TabularInline):
    model  = Nota
    extra  = 0
    fields = ('titulo', 'tipo', 'porcentaje', 'valor_obtenido',
              'fecha_limite', 'prioridad')


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'semestre', 'creditos', 'escala_notas',
                     'nota_minima_aprobacion', 'estado', 'color_preview',
                     'total_notas_ingresadas')
    list_filter   = ('estado', 'escala_notas')
    search_fields = ('nombre', 'semestre__perfil__usuario__email')
    inlines       = [NotaInline]

    def color_preview(self, obj):
        return format_html(
            '<span style="display:inline-block;width:20px;height:20px;'
            'background:{};border-radius:4px;border:1px solid #ccc"></span> {}',
            obj.color, obj.color
        )
    color_preview.short_description = 'Color'

    def total_notas_ingresadas(self, obj):
        con_nota = obj.notas.filter(valor_obtenido__isnull=False).count()
        total    = obj.total_notas
        color    = 'green' if con_nota == total else 'orange'
        return format_html(
            '<span style="color:{}">{}/{}</span>', color, con_nota, total
        )
    total_notas_ingresadas.short_description = 'Notas'

# NOTA


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'materia', 'tipo', 'porcentaje',
                     'valor_obtenido', 'fecha_limite', 'prioridad',
                     'estado_nota')
    list_filter   = ('tipo', 'prioridad')
    search_fields = ('titulo', 'materia__nombre',
                     'materia__semestre__perfil__usuario__email')
    date_hierarchy = 'fecha_limite'

    def estado_nota(self, obj):
        if obj.valor_obtenido is None:
            return format_html('<span style="color:gray"> Sin nota</span>')
        escala = float(obj.materia.escala_notas)
        minima = float(obj.materia.nota_minima_aprobacion)
        valor  = float(obj.valor_obtenido)
        if valor >= minima:
            return format_html(
                '<span style="color:green;font-weight:bold"> {}</span>', valor
            )
        return format_html(
            '<span style="color:red;font-weight:bold"> {}</span>', valor
        )
    estado_nota.short_description = 'Estado'

# TAREA


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'semestre', 'prioridad', 'estado',
                     'fecha_limite', 'estado_visual')
    list_filter   = ('prioridad', 'estado')
    search_fields = ('titulo', 'semestre__perfil__usuario__email')
    date_hierarchy = 'fecha_limite'

    actions = ['marcar_entregadas', 'marcar_pendientes']

    def estado_visual(self, obj):
        colores = {
            'pendiente': ('#f59e0b', ),
            'entregada': ('#22c55e', ),
            'vencida':   ('#ef4444', ),
        }
        color, icono = colores.get(obj.estado, ('#6b7280', '?'))
        return format_html(
            '<span style="color:{}">{} {}</span>',
            color, icono, obj.get_estado_display()
        )
    estado_visual.short_description = 'Estado'

    @admin.action(description='Marcar como entregadas')
    def marcar_entregadas(self, request, queryset):
        queryset.update(estado='entregada')
        self.message_user(request, f'{queryset.count()} tarea(s) marcada(s) como entregadas.')

    @admin.action(description='Marcar como pendientes')
    def marcar_pendientes(self, request, queryset):
        queryset.update(estado='pendiente')
        self.message_user(request, f'{queryset.count()} tarea(s) marcada(s) como pendientes.')

# HORARIO


@admin.register(ClaseHorario)
class ClaseHorarioAdmin(admin.ModelAdmin):
    list_display  = ('nombre_materia', 'perfil', 'dia_display',
                     'hora_inicio', 'duracion', 'salon', 'color_preview')
    list_filter   = ('dia',)
    search_fields = ('nombre_materia', 'perfil__usuario__email')
    ordering      = ('dia', 'hora_inicio')

    def dia_display(self, obj):
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        return dias[obj.dia] if obj.dia < len(dias) else obj.dia
    dia_display.short_description = 'Día'

    def color_preview(self, obj):
        return format_html(
            '<span style="display:inline-block;width:20px;height:20px;'
            'background:{};border-radius:4px;border:1px solid #ccc"></span>',
            obj.color
        )
    color_preview.short_description = 'Color'

# CONFIGURACIÓN DEL ADMIN


admin.site.site_header  = ' AcadémicoPro — Panel de Administración'
admin.site.site_title   = 'AcadémicoPro Admin'
admin.site.index_title  = 'Bienvenido al panel de administración'