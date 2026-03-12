
from django.db import models
from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError




class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un email")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50, blank=True)
    edad = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        null=True,
        blank=True
    )
    email = models.EmailField(unique=True)

    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
        ('P', 'Prefiero no decirlo'),
    ]
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, default='P', blank=True)

    TIPO_ESTUDIANTE_CHOICES = [
        ('C', 'Colegio'),
        ('U', 'Universidad'),
    ]
    tipo_estudiante = models.CharField(
        max_length=1, choices=TIPO_ESTUDIANTE_CHOICES, null=True, blank=False
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    intentos_fallidos = models.PositiveIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.email




class PerfilUniversitario(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, related_name='perfil_universitario'
    )
    universidad = models.CharField(max_length=100)
    carrera = models.CharField(max_length=100)
    facultad = models.CharField(max_length=100, blank=True, default='')
    modalidad = models.CharField(max_length=50, blank=True, default='')
    creditos_para_graduarse = models.PositiveIntegerField()
    creditos_minimos_por_semestre = models.PositiveIntegerField()
    creditos_maximos_por_semestre = models.PositiveIntegerField()
    semestre_actual = models.PositiveIntegerField()
    total_semestres = models.PositiveIntegerField(default=10)
    creditos_aprobados = models.PositiveIntegerField(default=0)
    promedio_minimo_carrera = models.DecimalField(max_digits=4, decimal_places=2, default=3.0)
    escala_notas = models.CharField(max_length=5, default='5.0')
    nota_minima_global = models.DecimalField(max_digits=5, decimal_places=2, default=3.0)
    anno_ingreso = models.PositiveIntegerField(null=True, blank=True)

    def clean(self):
        if self.creditos_minimos_por_semestre > self.creditos_maximos_por_semestre:
            raise ValidationError("El mínimo de créditos no puede superar el máximo.")

    @property
    def semestres_minimos(self):
        if self.creditos_minimos_por_semestre > 0:
            import math
            return math.ceil(self.creditos_para_graduarse / self.creditos_minimos_por_semestre)
        return 0

    @property
    def creditos_faltantes(self):
        return self.creditos_para_graduarse - self.creditos_aprobados

    class Meta:
        verbose_name = "Perfil Universitario"
        verbose_name_plural = "Perfiles Universitarios"

    def __str__(self):
        return f"{self.usuario.email} - {self.carrera}"




class PerfilSecundaria(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, related_name='perfil_secundaria'
    )
    nombre_instituto = models.CharField(max_length=100)
    curso_actual = models.CharField(max_length=100)
    total_de_periodos = models.PositiveIntegerField()
    periodo_actual = models.PositiveIntegerField()
    total_de_materias = models.PositiveIntegerField()
    total_de_materias_para_aprobacion = models.PositiveIntegerField()

    def clean(self):
        if self.periodo_actual > self.total_de_periodos:
            raise ValidationError("El periodo actual no puede superar el total de periodos.")

    class Meta:
        verbose_name = "Perfil Secundaria"
        verbose_name_plural = "Perfiles Secundaria"

    def __str__(self):
        return f"{self.usuario.email} - {self.curso_actual}"




class Semestre(models.Model):
    ESTADO_CHOICES = [
        ('en_curso', 'En curso'),
        ('completado', 'Completado'),
        ('pendiente', 'Pendiente'),
    ]
    perfil = models.ForeignKey(
        PerfilUniversitario, on_delete=models.CASCADE, related_name='semestres'
    )
    numero = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    class Meta:
        verbose_name = "Semestre"
        verbose_name_plural = "Semestres"
        ordering = ['numero']
        unique_together = ['perfil', 'numero']

    def __str__(self):
        return f"Semestre {self.numero} - {self.perfil.usuario.email}"



# MATERIA

class Materia(models.Model):
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('aprobada', 'Aprobada'),
        ('perdida', 'Perdida'),
    ]
    ESCALA_CHOICES = [
        ('5.0', 'Sobre 5.0'),
        ('10.0', 'Sobre 10.0'),
        ('100', 'Sobre 100'),
    ]
    semestre = models.ForeignKey(
        Semestre, on_delete=models.CASCADE, related_name='materias'
    )
    nombre = models.CharField(max_length=100)
    creditos = models.PositiveIntegerField()
    total_notas = models.PositiveIntegerField()
    escala_notas = models.CharField(max_length=5, choices=ESCALA_CHOICES, default='5.0')
    nota_minima_aprobacion = models.DecimalField(max_digits=5, decimal_places=2)
    color = models.CharField(max_length=7, default='#2563eb')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activa')

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"

    def __str__(self):
        return f"{self.nombre} - {self.semestre}"



# NOTA (actividad)


class Nota(models.Model):
    TIPO_CHOICES = [
        ('examen', 'Examen'),
        ('parcial', 'Parcial'),
        ('tarea', 'Tarea'),
        ('proyecto', 'Proyecto'),
        ('quiz', 'Quiz'),
        ('otro', 'Otro'),
    ]
    PRIORIDAD_CHOICES = [
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]

    materia = models.ForeignKey(
        Materia, on_delete=models.CASCADE, related_name='notas'
    )
    titulo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='otro')
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    valor_obtenido = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    descripcion = models.TextField(blank=True)
    fecha_limite = models.DateField(null=True, blank=True)
    recordatorio = models.TextField(blank=True)  # texto libre de recordatorio
    prioridad = models.CharField(
        max_length=5, choices=PRIORIDAD_CHOICES, default='media'
    )

    def clean(self):
        if self.valor_obtenido is not None:
            escala = float(self.materia.escala_notas)
            if self.valor_obtenido < 0 or self.valor_obtenido > escala:
                raise ValidationError(f"La nota debe estar entre 0 y {escala}")

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"

    def __str__(self):
        return f"{self.titulo} - {self.materia.nombre}"
# TAREA

class Tarea(models.Model):
    PRIORIDAD_CHOICES = [
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('entregada', 'Entregada'),
        ('vencida', 'Vencida'),
    ]
    semestre = models.ForeignKey(
        Semestre, on_delete=models.CASCADE, related_name='tareas'
    )
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    prioridad = models.CharField(max_length=5, choices=PRIORIDAD_CHOICES, default='media')
    fecha_limite = models.DateTimeField(null=True, blank=True)
    recordatorio = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')

    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"

    def __str__(self):
        return f"{self.titulo} - {self.semestre}"
# HORARIO
class ClaseHorario(models.Model):
    DIA_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
    ]

    perfil = models.ForeignKey(
        PerfilUniversitario, on_delete=models.CASCADE, related_name='horario'
    )
    materia = models.ForeignKey(
        Materia, on_delete=models.CASCADE, related_name='clases_horario',
        null=True, blank=True
    )
    nombre_materia = models.CharField(max_length=100)  # cache por si se borra la materia
    color = models.CharField(max_length=7, default='#2563eb')
    dia = models.IntegerField(choices=DIA_CHOICES)
    hora_inicio = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(23)]
    )
    duracion = models.IntegerField(
        default=2, validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    salon = models.CharField(max_length=100, blank=True)

    def clean(self):
        # Verificar solapamiento en el mismo día
        solapamientos = ClaseHorario.objects.filter(
            perfil=self.perfil,
            dia=self.dia
        ).exclude(pk=self.pk)

        for clase in solapamientos:
            if (self.hora_inicio < clase.hora_inicio + clase.duracion and
                    self.hora_inicio + self.duracion > clase.hora_inicio):
                raise ValidationError(
                    f"Solapamiento con {clase.nombre_materia} a las {clase.hora_inicio}:00"
                )

    class Meta:
        verbose_name = "Clase en Horario"
        verbose_name_plural = "Clases en Horario"
        ordering = ['dia', 'hora_inicio']

    def __str__(self):
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        return f"{self.nombre_materia} - {dias[self.dia]} {self.hora_inicio}:00"