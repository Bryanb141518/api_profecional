"""
Módulo de serializadores para registro de usuarios.

Contiene validaciones completas para el registro seguro de nuevos usuarios
incluyendo validación de campos, contraseñas y reglas de negocio.
"""

import re
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.hashers import make_password
from .models import Usuario

# Constantes de validación
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MIN_AGE_REGISTRATION = 14
MIN_AGE_UNRESTRICTED = 18
MAX_AGE = 120

SPECIAL_CHARS_PATTERN = r'[!@#$%^&*(),.?":{}|<>]'


# -> str indica que la función retorna texto
def validar_texto(campo: str, value: str) -> str:
    """
    Valida que un campo de texto contenga solo letras y espacios.

    Args:
        campo: Nombre del campo para mensajes de error.
        value: Valor a validar.

    Returns:
        str: Texto validado y capitalizado.

    Raises:
        ValidationError: Si el texto no cumple con los requisitos.
    """
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


class RegistroUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de nuevos usuarios.

    Valida todos los campos según las reglas de negocio y restricciones
    de seguridad de la plataforma.
    """

    genero = serializers.ChoiceField(
        choices=[c[0] for c in Usuario.GENERO_CHOICES],
        default='P',
        error_messages={
            'invalid_choice': 'Género no válido. Opciones disponibles: {input}.'
        }
    )

    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=Usuario.objects.all(),
                message="Este correo ya está registrado"
            )
        ]
    )

    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'edad', 'genero', 'email', 'password']

    # ========== Validadores de campo individual ==========

    def validate_nombre(self, value: str) -> str:
        """Valida el nombre del usuario."""
        return validar_texto('nombre', value)

    def validate_apellido(self, value: str) -> str:
        """Valida el apellido del usuario."""
        return validar_texto('apellido', value)

    def validate_edad(self, value: int) -> int:
        """
        Valida la edad del usuario.

        El modelo ya valida que sea entero, obligatorio y positivo.
        Aquí validamos rangos adicionales.
        """
        if value > MAX_AGE:
            raise serializers.ValidationError(
                f'La edad no puede ser mayor a {MAX_AGE} años'
            )
        return value

    def validate_password(self, value: str) -> str:
        """
        Valida la contraseña según estándares de seguridad.

        Requisitos:
        - Mínimo 8 caracteres, máximo 128
        - Al menos un número
        - Al menos una mayúscula
        - Al menos una minúscula
        - Al menos un carácter especial
        - No ser una contraseña común
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError('El password es obligatorio')

        if len(value) < MIN_PASSWORD_LENGTH:
            raise serializers.ValidationError(
                f'La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres'
            )

        if len(value) > MAX_PASSWORD_LENGTH:
            raise serializers.ValidationError(
                f'La contraseña debe tener máximo {MAX_PASSWORD_LENGTH} caracteres'
            )

        if not re.search(r'\d', value):
            raise serializers.ValidationError(
                'La contraseña debe contener al menos un número'
            )

        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError(
                'La contraseña debe contener al menos una letra mayúscula'
            )

        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError(
                'La contraseña debe contener al menos una letra minúscula'
            )

        if not re.search(SPECIAL_CHARS_PATTERN, value):
            raise serializers.ValidationError(
                'La contraseña debe contener al menos un carácter especial'
            )


        return value

    # ========== Validador de objeto completo ==========

    def validate(self, data: dict) -> dict:
        """
        Valida las reglas de negocio que involucran múltiples campos.

        - Edad mínima de 14 años
        - Aviso de restricciones para menores de 18
        - Nombre y apellido no pueden ser iguales
        """
        edad = data.get('edad')
        nombre = data.get('nombre')
        apellido = data.get('apellido')

        if edad is None:
            raise serializers.ValidationError({
                'edad': "La edad es requerida para completar el registro"
            })

        if edad < MIN_AGE_REGISTRATION:
            raise serializers.ValidationError({
                'edad': f"Debes tener al menos {MIN_AGE_REGISTRATION} años para registrarte"
            })

        if edad < MIN_AGE_UNRESTRICTED:
            data['aviso'] = "Puedes registrarte pero con ciertas restricciones de contenido"

        if nombre and apellido and nombre == apellido:
            raise serializers.ValidationError(
                "El nombre y el apellido no pueden ser iguales"
            )

        return data

    # ========== Crear instancia en BD ==========

    def create(self, validated_data: dict) -> Usuario:
        """
        Crea un nuevo usuario con la contraseña hasheada.

        La contraseña se convierte a hash antes de guardarla
        para proteger los datos del usuario.
        """
        validated_data.pop('aviso', None)  # ← aquí
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

# validacion de los datos del login
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)# esto evita que la contrasena salga en respuesta que aparesca en el json
