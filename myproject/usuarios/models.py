from django.db import models
from django.contrib.auth.models import  PermissionsMixin ,AbstractBaseUser, BaseUserManager
#evitar valores absurdos del usuario
from django.core.validators import MinValueValidator, MaxValueValidator


# Primero el manager para manejar creación de usuarios
class UsuarioManager(BaseUserManager):
    # el extra fields perimite el ingreso de mas atributos pero solo tomara en cuanta los dos declarados
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un email")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Hashea la contraseña
        user.save(using=self._db)
        return user
# crear un super usuario en terminal pedira correo y contrasena tranda permisos especiales
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50,blank=True)
    edad = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        null=True,
        blank=True
    )
    # valida que tenga el formato de correo prohibir que existan dos usario con el mismo correo
    email = models.EmailField(unique=True)

    # 1. Definimos las opciones fuera (es más limpio)
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
        ('P', 'Prefiero no decirlo'),
    ]

    # 2. La usamos aquí
    genero = models.CharField(
        max_length=1,
        choices=GENERO_CHOICES,
        default='P',
        blank=True
    )

    TIPO_ESTUDIANTE_CHOICES = [
        ('C', 'Colegio'),
        ('U', 'Universidad'),
    ]

    tipo_estudiante = models.CharField(
        max_length=1,
        choices=TIPO_ESTUDIANTE_CHOICES,
        null=True,
        blank=True
    )

    # activar y desactivar usuario
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    #cambiar el modelo de usario por defecto y coloca el que delcaro para las peticiones con bd
    objects = UsuarioManager()

    USERNAME_FIELD = 'email'  # Usar correo como username
    REQUIRED_FIELDS = ['nombre']

    # definicionde como se van a mostrar los datos
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.email

