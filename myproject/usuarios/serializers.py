"""
Serializadores completos para el sistema académico.
"""

import re
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.hashers import make_password
from .models import (
    Usuario, PerfilUniversitario, PerfilSecundaria,
    Semestre, Materia, Nota, Tarea, ClaseHorario
)

# ── Constantes ─────────────────────────────────────────
MIN_PASSWORD_LENGTH  = 8
MAX_PASSWORD_LENGTH  = 128
MIN_AGE_REGISTRATION = 14
MIN_AGE_UNRESTRICTED = 18
MAX_AGE              = 120
SPECIAL_CHARS_PATTERN = r'[!@#$%^&*(),.?":{}|<>]'


def validar_texto(campo: str, value: str) -> str:
    value = value.strip()
    if not value:
        raise serializers.ValidationError(f'El {campo} es obligatorio')
    if any(char.isdigit() for char in value):
        raise serializers.ValidationError(f'El {campo} no puede contener números')
    if not all(char.isalpha() or char.isspace() for char in value):
        raise serializers.ValidationError(
            f'El {campo} solo puede contener letras y espacios'
        )
    return ' '.join(word.capitalize() for word in value.split())

# AUTH

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    genero = serializers.ChoiceField(
        choices=[c[0] for c in Usuario.GENERO_CHOICES],
        default='P',
        error_messages={'invalid_choice': 'Género no válido.'}
    )
    email = serializers.EmailField(
        validators=[UniqueValidator(
            queryset=Usuario.objects.all(),
            message="Este correo ya está registrado"
        )]
    )
    password = serializers.CharField(write_only=True)

    class Meta:
        model  = Usuario
        fields = ['nombre', 'apellido', 'edad', 'genero', 'email', 'password']

    def validate_nombre(self, value):
        return validar_texto('nombre', value)

    def validate_apellido(self, value):
        return validar_texto('apellido', value)

    def validate_edad(self, value):
        if value > MAX_AGE:
            raise serializers.ValidationError(f'La edad no puede ser mayor a {MAX_AGE} años')
        return value

    def validate_password(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El password es obligatorio')
        if len(value) < MIN_PASSWORD_LENGTH:
            raise serializers.ValidationError(
                f'La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres')
        if len(value) > MAX_PASSWORD_LENGTH:
            raise serializers.ValidationError(
                f'La contraseña debe tener máximo {MAX_PASSWORD_LENGTH} caracteres')
        if not re.search(r'\d', value):
            raise serializers.ValidationError('La contraseña debe contener al menos un número')
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError('La contraseña debe contener al menos una minúscula')
        if not re.search(SPECIAL_CHARS_PATTERN, value):
            raise serializers.ValidationError('La contraseña debe contener al menos un carácter especial')
        return value

    def validate(self, data):
        edad    = data.get('edad')
        nombre  = data.get('nombre')
        apellido= data.get('apellido')

        if edad is None:
            raise serializers.ValidationError({'edad': "La edad es requerida"})
        if edad < MIN_AGE_REGISTRATION:
            raise serializers.ValidationError(
                {'edad': f"Debes tener al menos {MIN_AGE_REGISTRATION} años para registrarte"})
        if edad < MIN_AGE_UNRESTRICTED:
            data['aviso'] = "Puedes registrarte pero con ciertas restricciones de contenido"
        if nombre and apellido and nombre == apellido:
            raise serializers.ValidationError("El nombre y el apellido no pueden ser iguales")
        return data

    def create(self, validated_data):
        validated_data.pop('aviso', None)
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TipoEstudianteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Usuario
        fields = ['tipo_estudiante']

# PERFIL UNIVERSITARIO


class PerfilUniversitarioSerializer(serializers.ModelSerializer):
    semestres_minimos = serializers.ReadOnlyField()
    creditos_faltantes = serializers.ReadOnlyField()
    # Datos del usuario incluidos en la respuesta
    nombre_usuario = serializers.SerializerMethodField()
    email_usuario  = serializers.SerializerMethodField()

    class Meta:
        model  = PerfilUniversitario
        fields = [
            'universidad', 'carrera', 'facultad', 'modalidad',
            'creditos_para_graduarse', 'creditos_minimos_por_semestre',
            'creditos_maximos_por_semestre', 'semestre_actual', 'total_semestres',
            'creditos_aprobados', 'promedio_minimo_carrera',
            'escala_notas', 'nota_minima_global', 'anno_ingreso',
            'semestres_minimos', 'creditos_faltantes',
            'nombre_usuario', 'email_usuario',
        ]
        read_only_fields = ['creditos_aprobados']

    def get_nombre_usuario(self, obj):
        return f"{obj.usuario.nombre} {obj.usuario.apellido}".strip()

    def get_email_usuario(self, obj):
        return obj.usuario.email

    def validate(self, attrs):
        user = self.context['request'].user
        if user.tipo_estudiante != 'U':
            raise serializers.ValidationError(
                "Solo usuarios universitarios pueden crear este perfil.")
        if not self.instance and hasattr(user, 'perfil_universitario'):
            raise serializers.ValidationError(
                "Este usuario ya tiene perfil universitario.")
        cmin = attrs.get('creditos_minimos_por_semestre')
        cmax = attrs.get('creditos_maximos_por_semestre')
        if cmin and cmax and cmin > cmax:
            raise serializers.ValidationError(
                "El mínimo de créditos no puede superar el máximo.")
        return attrs

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


# PERFIL SECUNDARIA


class PerfilSecundariaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PerfilSecundaria
        fields = [
            'nombre_instituto', 'curso_actual', 'total_de_periodos',
            'periodo_actual', 'total_de_materias', 'total_de_materias_para_aprobacion'
        ]
        read_only_fields = ['usuario']

    def validate(self, attrs):
        user = self.context['request'].user
        if user.tipo_estudiante != 'C':
            raise serializers.ValidationError(
                "Solo usuarios de secundaria pueden crear este perfil.")
        if hasattr(user, 'perfil_secundaria'):
            raise serializers.ValidationError(
                "Este usuario ya tiene perfil de secundaria.")
        if attrs['periodo_actual'] > attrs['total_de_periodos']:
            raise serializers.ValidationError(
                "El periodo actual no puede superar el total de periodos.")
        return attrs


# SEMESTRE

class SemestreSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Semestre
        fields = ['id', 'numero', 'estado']

    def validate(self, attrs):
        perfil = self.context.get('perfil')
        numero = attrs.get('numero')
        if numero is not None and numero < 1:
            raise serializers.ValidationError(
                "El número de semestre debe ser mayor a 0.")
        # Solo validar duplicado en creación
        if perfil and not self.instance:
            if Semestre.objects.filter(perfil=perfil, numero=numero).exists():
                raise serializers.ValidationError(
                    "Ya existe un semestre con ese número.")
        return attrs

# NOTA

class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Nota
        fields = [
            'id', 'titulo', 'tipo', 'porcentaje', 'valor_obtenido',
            'descripcion', 'fecha_limite', 'recordatorio', 'prioridad'
        ]

    def validate_porcentaje(self, value):
        if value <= 0 or value > 100:
            raise serializers.ValidationError(
                "El porcentaje debe estar entre 1 y 100.")
        return value

    def validate(self, attrs):
        valor   = attrs.get('valor_obtenido')
        materia = self.context.get('materia')
        if valor is not None and materia:
            escala = float(materia.escala_notas)
            if valor < 0 or valor > escala:
                raise serializers.ValidationError(
                    f"La nota debe estar entre 0 y {escala}.")

        # Validar que el porcentaje total de la materia no supere 100
        if materia and not self.instance:
            porcentaje_nuevo = attrs.get('porcentaje', 0)
            porcentaje_actual = sum(
                float(n.porcentaje) for n in materia.notas.all()
            )
            if porcentaje_actual + float(porcentaje_nuevo) > 100:
                raise serializers.ValidationError(
                    f"El porcentaje total superaría 100%. Disponible: {100 - porcentaje_actual}%")
        return attrs

# MATERIA
class MateriaSerializer(serializers.ModelSerializer):
    notas = NotaSerializer(many=True, read_only=True)

    class Meta:
        model  = Materia
        fields = [
            'id', 'nombre', 'creditos', 'total_notas', 'escala_notas',
            'nota_minima_aprobacion', 'color', 'estado', 'notas'
        ]
        read_only_fields = ['estado']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and hasattr(request.user, 'perfil_universitario'):
            perfil   = request.user.perfil_universitario
            creditos = attrs.get('creditos', getattr(self.instance, 'creditos', 0))
            if creditos > perfil.creditos_maximos_por_semestre:
                raise serializers.ValidationError(
                    f"Los créditos no pueden superar el máximo por semestre "
                    f"({perfil.creditos_maximos_por_semestre}).")
        return attrs

# TAREA

class TareaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tarea
        fields = [
            'id', 'titulo', 'descripcion', 'prioridad',
            'fecha_limite', 'recordatorio', 'estado'
        ]
# HORARIO
class ClaseHorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ClaseHorario
        fields = [
            'id', 'materia', 'nombre_materia', 'color',
            'dia', 'hora_inicio', 'duracion', 'salon'
        ]

    def validate(self, attrs):
        perfil     = self.context.get('perfil')
        dia        = attrs.get('dia')
        hora_inicio= attrs.get('hora_inicio')
        duracion   = attrs.get('duracion', 2)

        if perfil:
            solapamientos = ClaseHorario.objects.filter(
                perfil=perfil, dia=dia
            )
            if self.instance:
                solapamientos = solapamientos.exclude(pk=self.instance.pk)

            for clase in solapamientos:
                if (hora_inicio < clase.hora_inicio + clase.duracion and
                        hora_inicio + duracion > clase.hora_inicio):
                    raise serializers.ValidationError(
                        f"Solapamiento con '{clase.nombre_materia}' "
                        f"a las {clase.hora_inicio}:00")
        return attrs
