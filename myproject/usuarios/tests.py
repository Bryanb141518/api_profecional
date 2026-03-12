from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from .models import Usuario
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import ValidationError
from .models import PerfilUniversitario, PerfilSecundaria
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Semestre, Materia, Nota, Tarea
class RegistroUsuarioTestCase(APITestCase):

    def setUp(self):
        self.url = reverse('registro')
        self.datos_validos = {
            "nombre": "Juan",
            "apellido": "Perez",
            "edad": 20,
            "genero": "M",
            "email": "juan@gmail.com",
            "password": "Abc123!@"
        }

    # ========== Registro exitoso ==========

    def test_registro_exitoso(self):
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ========== Validaciones de nombre ==========

    def test_nombre_con_numeros(self):
        self.datos_validos['nombre'] = 'Juan123'
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nombre_vacio(self):
        self.datos_validos['nombre'] = ''
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========== Validaciones de edad ==========

    def test_edad_menor_a_14(self):
        self.datos_validos['edad'] = 10
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edad_mayor_a_120(self):
        self.datos_validos['edad'] = 150
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========== Validaciones de contraseña ==========

    def test_password_sin_mayuscula(self):
        self.datos_validos['password'] = 'abc123!@'
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_sin_numero(self):
        self.datos_validos['password'] = 'Abcdef!@'
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_sin_caracter_especial(self):
        self.datos_validos['password'] = 'Abcdef123'
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========== Validaciones de negocio ==========

    def test_email_duplicado(self):
        self.client.post(self.url, self.datos_validos, format='json')
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nombre_igual_apellido(self):
        self.datos_validos['nombre'] = 'Juan'
        self.datos_validos['apellido'] = 'Juan'
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTestCase(APITestCase):

    def setUp(self):
        self.url = reverse('login')
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan@gmail.com",
            password=make_password("Abc123!@")
        )
        self.datos_validos = {
            "email": "juan@gmail.com",
            "password": "Abc123!@"
        }

    # ========== Login exitoso ==========

    def test_login_exitoso(self):
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    # ========== Credenciales incorrectas ==========

    def test_email_no_existe(self):
        self.datos_validos['email'] = 'noexiste@gmail.com'
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_incorrecta(self):
        self.datos_validos['password'] = 'Incorrecta123!@'
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ========== Token no expone contraseña ==========

    def test_password_no_en_respuesta(self):
        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertNotIn('password', response.data)

    # ========== Bloqueo por intentos fallidos ==========

    def test_bloqueo_despues_de_5_intentos(self):
        for _ in range(5):
            self.client.post(self.url, {
                'email': 'juan@gmail.com',
                'password': 'ContraseñaWrong1!'
            }, format='json')

        response = self.client.post(self.url, {
            'email': 'juan@gmail.com',
            'password': 'ContraseñaWrong1!'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_exitoso_resetea_intentos(self):
        for _ in range(2):
            self.client.post(self.url, {
                'email': 'juan@gmail.com',
                'password': 'ContraseñaWrong1!'
            }, format='json')

        self.client.post(self.url, self.datos_validos, format='json')

        usuario = Usuario.objects.get(email='juan@gmail.com')
        self.assertEqual(usuario.intentos_fallidos, 0)
        self.assertIsNone(usuario.bloqueado_hasta)

    def test_cuenta_bloqueada_no_permite_login(self):
        from django.utils import timezone
        from datetime import timedelta
        self.usuario.bloqueado_hasta = timezone.now() + timedelta(minutes=30)
        self.usuario.save()

        response = self.client.post(self.url, self.datos_validos, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
class TipoEstudianteTestCase(APITestCase):

    def setUp(self):
        self.url = reverse('tipo-estudiante')
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan@gmail.com",
            password=make_password("Abc123!@")
        )
        refresh = RefreshToken.for_user(self.usuario)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    # ========== Exitosos ==========

    def test_tipo_colegio(self):
        response = self.client.post(self.url, {"tipo_estudiante": "C"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_tipo_universidad(self):
        response = self.client.post(self.url, {"tipo_estudiante": "U"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ========== Errores ==========

    def test_tipo_invalido(self):
        response = self.client.post(self.url, {"tipo_estudiante": "X"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sin_token(self):
        self.client.credentials()
        response = self.client.post(self.url, {"tipo_estudiante": "C"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_campo_vacio(self):
        response = self.client.post(self.url, {"tipo_estudiante": ""}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PerfilUniversitarioTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan@gmail.com",
            password=make_password("Abc123!@")
        )

    def test_creacion_perfil_universitario_exitoso(self):
        perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=5,
            creditos_aprobados=80,
            promedio_minimo_carrera=3.0
        )
        self.assertEqual(perfil.semestre_actual, 5)

    def test_creditos_minimos_mayor_que_maximos(self):
        perfil = PerfilUniversitario(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=25,
            creditos_maximos_por_semestre=20,
            semestre_actual=5,
            creditos_aprobados=80,
            promedio_minimo_carrera=3.0
        )
        with self.assertRaises(ValidationError):
            perfil.full_clean()

    def test_semestres_minimos_calculados(self):
        perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=5,
            creditos_aprobados=80,
            promedio_minimo_carrera=3.0
        )
        self.assertEqual(perfil.semestres_minimos, 8)

class PerfilSecundariaTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Ana",
            apellido="Gomez",
            edad=16,
            genero="F",
            email="ana@gmail.com",
            password=make_password("Abc123!@")
        )

    def test_creacion_perfil_secundaria_exitoso(self):
        perfil = PerfilSecundaria.objects.create(
            usuario=self.usuario,
            nombre_instituto="Colegio ABC",
            curso_actual="11°",
            total_de_periodos=4,
            periodo_actual=2,
            total_de_materias=12,
            total_de_materias_para_aprobacion=10
        )

        self.assertEqual(perfil.periodo_actual, 2)

    def test_periodo_mayor_que_total(self):
        perfil = PerfilSecundaria(
            usuario=self.usuario,
            nombre_instituto="Colegio ABC",
            curso_actual="11°",
            total_de_periodos=3,
            periodo_actual=5,
            total_de_materias=12,
            total_de_materias_para_aprobacion=10
        )

        with self.assertRaises(ValidationError):
            perfil.full_clean()

class LogoutTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Ana",
            apellido="Gomez",
            edad=16,
            genero="F",
            email="ana@gmail.com",
            password=make_password("Abc123!@")
        )
        refresh = RefreshToken.for_user(self.usuario)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)
        self.url = '/api/logout/'

        # segundo usuario para el test de token ajeno
        self.usuario2 = Usuario.objects.create(
            nombre="Pedro",
            apellido="Lopez",
            edad=20,
            genero="M",
            email="pedro@gmail.com",
            password=make_password("Abc123!@")
        )
        refresh2 = RefreshToken.for_user(self.usuario2)
        self.refresh_token_usuario2 = str(refresh2)
        self.access_token_usuario2 = str(refresh2.access_token)

    def test_logout_exitoso(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, 205)

    def test_logout_sin_refresh_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)

    def test_logout_token_ya_revocado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        self.client.post(self.url, {'refresh': self.refresh_token})
        response = self.client.post(self.url, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, 400)

    def test_logout_sin_autenticacion(self):
        response = self.client.post(self.url, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, 401)

    def test_logout_con_token_de_otro_usuario(self):
        # Ana intenta hacer logout con el token de Pedro
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url, {'refresh': self.refresh_token_usuario2})
        self.assertEqual(response.status_code, 403)


# ========== Semestre ==========
class SemestreTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_semestre@gmail.com",
            password=make_password("Abc123!@")
        )
        self.perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )

    def test_creacion_semestre_exitoso(self):
        semestre = Semestre.objects.create(
            perfil=self.perfil,
            numero=1
        )
        self.assertEqual(semestre.numero, 1)
        self.assertEqual(semestre.estado, 'pendiente')

    def test_semestre_duplicado(self):
        Semestre.objects.create(perfil=self.perfil, numero=1)
        with self.assertRaises(Exception):
            Semestre.objects.create(perfil=self.perfil, numero=1)

    def test_semestre_estado_por_defecto(self):
        semestre = Semestre.objects.create(perfil=self.perfil, numero=1)
        self.assertEqual(semestre.estado, 'pendiente')


# ========== Materia ==========
class MateriaTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_materia@gmail.com",
            password=make_password("Abc123!@")
        )
        self.perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )
        self.semestre = Semestre.objects.create(perfil=self.perfil, numero=1)

    def test_creacion_materia_exitosa(self):
        materia = Materia.objects.create(
            semestre=self.semestre,
            nombre="Cálculo I",
            creditos=3,
            total_notas=3,
            escala_notas='5.0',
            nota_minima_aprobacion=3.0,
            color='#FF5733'
        )
        self.assertEqual(materia.nombre, "Cálculo I")
        self.assertEqual(materia.estado, 'activa')

    def test_estado_por_defecto_activa(self):
        materia = Materia.objects.create(
            semestre=self.semestre,
            nombre="Física I",
            creditos=3,
            total_notas=3,
            escala_notas='5.0',
            nota_minima_aprobacion=3.0,
            color='#000000'
        )
        self.assertEqual(materia.estado, 'activa')


# ========== Nota ==========
class NotaTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_nota@gmail.com",
            password=make_password("Abc123!@")
        )
        self.perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )
        self.semestre = Semestre.objects.create(perfil=self.perfil, numero=1)
        self.materia = Materia.objects.create(
            semestre=self.semestre,
            nombre="Cálculo I",
            creditos=3,
            total_notas=3,
            escala_notas='5.0',
            nota_minima_aprobacion=3.0,
            color='#000000'
        )

    def test_creacion_nota_exitosa(self):
        nota = Nota.objects.create(
            materia=self.materia,
            titulo="Parcial 1",
            porcentaje=30,
            valor_obtenido=4.5
        )
        self.assertEqual(nota.titulo, "Parcial 1")
        self.assertEqual(nota.valor_obtenido, 4.5)

    def test_nota_fuera_de_escala(self):
        nota = Nota(
            materia=self.materia,
            titulo="Parcial 1",
            porcentaje=30,
            valor_obtenido=6.0  # fuera de escala 5.0
        )
        with self.assertRaises(ValidationError):
            nota.full_clean()

    def test_nota_sin_valor_obtenido(self):
        nota = Nota.objects.create(
            materia=self.materia,
            titulo="Parcial 2",
            porcentaje=30,
            valor_obtenido=None
        )
        self.assertIsNone(nota.valor_obtenido)


# ========== Tarea ==========
class TareaTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_tarea@gmail.com",
            password=make_password("Abc123!@")
        )
        self.perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )
        self.semestre = Semestre.objects.create(perfil=self.perfil, numero=1)

    def test_creacion_tarea_exitosa(self):
        tarea = Tarea.objects.create(
            semestre=self.semestre,
            titulo="Entregar laboratorio",
            descripcion="Laboratorio de física",
            prioridad='alta'
        )
        self.assertEqual(tarea.titulo, "Entregar laboratorio")
        self.assertEqual(tarea.estado, 'pendiente')

    def test_estado_por_defecto_pendiente(self):
        tarea = Tarea.objects.create(
            semestre=self.semestre,
            titulo="Tarea 1",
            prioridad='media'
        )
        self.assertEqual(tarea.estado, 'pendiente')

    def test_prioridad_alta(self):
        tarea = Tarea.objects.create(
            semestre=self.semestre,
            titulo="Examen final",
            prioridad='alta'
        )
        self.assertEqual(tarea.prioridad, 'alta')

# ========== Perfil Universitario Detail ==========
class PerfilUniversitarioDetailTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_detail@gmail.com",
            password=make_password("Abc123!@")
        )
        self.usuario.tipo_estudiante = 'U'
        self.usuario.save()

        self.perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )

        refresh = RefreshToken.for_user(self.usuario)
        self.access_token = str(refresh.access_token)
        self.url_detalle = '/api/perfil-universitario/detalle/'

    def test_get_perfil_universitario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.url_detalle)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['universidad'], 'Universidad Nacional')

    def test_get_perfil_sin_autenticacion(self):
        response = self.client.get(self.url_detalle)
        self.assertEqual(response.status_code, 401)

    def test_put_perfil_universitario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.put(self.url_detalle, {
            'universidad': 'Universidad de los Andes',
            'carrera': 'Medicina',
            'creditos_para_graduarse': 180,
            'creditos_minimos_por_semestre': 18,
            'creditos_maximos_por_semestre': 24,
            'semestre_actual': 2,
            'promedio_minimo_carrera': 3.5
        }, format='json')
        self.assertEqual(response.status_code, 200)


# ========== Semestre View ==========
class SemestreViewTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_semestre_view@gmail.com",
            password=make_password("Abc123!@")
        )
        self.usuario.tipo_estudiante = 'U'
        self.usuario.save()

        self.perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )

        refresh = RefreshToken.for_user(self.usuario)
        self.access_token = str(refresh.access_token)
        self.url = '/api/semestres/'

    def test_crear_semestre(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url, {'numero': 1}, format='json')
        self.assertEqual(response.status_code, 201)

    def test_listar_semestres(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        Semestre.objects.create(perfil=self.perfil, numero=1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_semestre_duplicado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        self.client.post(self.url, {'numero': 1}, format='json')
        response = self.client.post(self.url, {'numero': 1}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_semestre_sin_autenticacion(self):
        response = self.client.post(self.url, {'numero': 1}, format='json')
        self.assertEqual(response.status_code, 401)


# ========== Materia View ==========
class MateriaViewTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_materia_view@gmail.com",
            password=make_password("Abc123!@")
        )
        self.usuario.tipo_estudiante = 'U'
        self.usuario.save()

        self.perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )

        self.semestre = Semestre.objects.create(perfil=self.perfil, numero=1)
        refresh = RefreshToken.for_user(self.usuario)
        self.access_token = str(refresh.access_token)
        self.url = f'/api/semestres/{self.semestre.id}/materias/'

    def test_crear_materia(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url, {
            'nombre': 'Cálculo I',
            'creditos': 3,
            'total_notas': 3,
            'escala_notas': '5.0',
            'nota_minima_aprobacion': 3.0,
            'color': '#FF5733'
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_listar_materias(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_materia_sin_autenticacion(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)


# ========== Nota View ==========
class NotaViewTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_nota_view@gmail.com",
            password=make_password("Abc123!@")
        )
        self.usuario.tipo_estudiante = 'U'
        self.usuario.save()

        self.perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )

        self.semestre = Semestre.objects.create(perfil=self.perfil, numero=1)
        self.materia = Materia.objects.create(
            semestre=self.semestre,
            nombre="Cálculo I",
            creditos=3,
            total_notas=3,
            escala_notas='5.0',
            nota_minima_aprobacion=3.0,
            color='#000000'
        )

        refresh = RefreshToken.for_user(self.usuario)
        self.access_token = str(refresh.access_token)
        self.url = f'/api/materias/{self.materia.id}/notas/'

    def test_crear_nota(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url, {
            'titulo': 'Parcial 1',
            'porcentaje': 30,
            'valor_obtenido': 4.5
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_listar_notas(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_nota_sin_autenticacion(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)


# ========== Tarea View ==========
class TareaViewTestCase(APITestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_tarea_view@gmail.com",
            password=make_password("Abc123!@")
        )
        self.usuario.tipo_estudiante = 'U'
        self.usuario.save()

        self.perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )

        self.semestre = Semestre.objects.create(perfil=self.perfil, numero=1)
        refresh = RefreshToken.for_user(self.usuario)
        self.access_token = str(refresh.access_token)
        self.url = f'/api/semestres/{self.semestre.id}/tareas/'

    def test_crear_tarea(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url, {
            'titulo': 'Entregar laboratorio',
            'descripcion': 'Laboratorio de física',
            'prioridad': 'alta'
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_listar_tareas(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_tarea_sin_autenticacion(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)


# ============================================
# Tests faltantes — Agregar al final de tests.py
# ============================================

from django.contrib.auth.hashers import make_password
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    Usuario, PerfilUniversitario, Semestre,
    Materia, Nota, ClaseHorario
)


# ========== Token Refresh ==========
class TokenRefreshTestCase(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_refresh@gmail.com",
            password=make_password("Abc123!@")
        )
        refresh = RefreshToken.for_user(self.usuario)
        self.refresh_token = str(refresh)
        self.url = '/api/token/refresh/'

    def test_refresh_exitoso(self):
        response = self.client.post(self.url, {'refresh': self.refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_token_invalido(self):
        response = self.client.post(self.url, {'refresh': 'token_falso'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_sin_token(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ========== DELETE Semestre, Materia, Nota ==========
class EliminarRecursosTestCase(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_delete@gmail.com",
            password=make_password("Abc123!@")
        )
        self.usuario.tipo_estudiante = 'U'
        self.usuario.save()
        self.perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )
        self.semestre = Semestre.objects.create(perfil=self.perfil, numero=1)
        self.materia = Materia.objects.create(
            semestre=self.semestre,
            nombre="Cálculo I",
            creditos=3,
            total_notas=3,
            escala_notas='5.0',
            nota_minima_aprobacion=3.0,
            color='#FF5733'
        )
        self.nota = Nota.objects.create(
            materia=self.materia,
            titulo="Parcial 1",
            porcentaje=30,
            valor_obtenido=4.0
        )
        refresh = RefreshToken.for_user(self.usuario)
        self.access_token = str(refresh.access_token)

    def test_eliminar_nota(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = f'/api/notas/{self.nota.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Nota.objects.filter(id=self.nota.id).exists())

    def test_eliminar_materia(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = f'/api/materias/{self.materia.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Materia.objects.filter(id=self.materia.id).exists())

    def test_eliminar_semestre(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = f'/api/semestres/{self.semestre.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Semestre.objects.filter(id=self.semestre.id).exists())

    def test_eliminar_sin_autenticacion(self):
        url = f'/api/notas/{self.nota.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ========== Horario (ClaseHorario) ==========
class HorarioTestCase(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_horario@gmail.com",
            password=make_password("Abc123!@")
        )
        self.usuario.tipo_estudiante = 'U'
        self.usuario.save()
        self.perfil = PerfilUniversitario.objects.create(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )
        refresh = RefreshToken.for_user(self.usuario)
        self.access_token = str(refresh.access_token)
        self.url = '/api/horario/'
        self.datos_clase = {
            'nombre_materia': 'Cálculo I',
            'color': '#FF5733',
            'dia': 1,
            'hora_inicio': 8,
            'duracion': 2,
            'salon': 'Aula 101'
        }

    def test_crear_clase_horario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.url, self.datos_clase, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_listar_horario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_editar_clase_horario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        clase = ClaseHorario.objects.create(perfil=self.perfil, **self.datos_clase)
        url = f'/api/horario/{clase.id}/'
        response = self.client.put(url, {**self.datos_clase, 'salon': 'Aula 202'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_eliminar_clase_horario(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        clase = ClaseHorario.objects.create(perfil=self.perfil, **self.datos_clase)
        url = f'/api/horario/{clase.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ClaseHorario.objects.filter(id=clase.id).exists())

    def test_horario_sin_autenticacion(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ========== Acceso Cruzado ==========
class AccesoCruzadoTestCase(APITestCase):
    def setUp(self):
        # Usuario 1
        self.usuario1 = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            edad=20,
            genero="M",
            email="juan_acceso@gmail.com",
            password=make_password("Abc123!@")
        )
        self.usuario1.tipo_estudiante = 'U'
        self.usuario1.save()
        self.perfil1 = PerfilUniversitario.objects.create(
            usuario=self.usuario1,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            creditos_para_graduarse=160,
            creditos_minimos_por_semestre=20,
            creditos_maximos_por_semestre=25,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.0
        )
        self.semestre1 = Semestre.objects.create(perfil=self.perfil1, numero=1)
        self.materia1 = Materia.objects.create(
            semestre=self.semestre1,
            nombre="Cálculo I",
            creditos=3,
            total_notas=3,
            escala_notas='5.0',
            nota_minima_aprobacion=3.0,
            color='#FF5733'
        )

        # Usuario 2
        self.usuario2 = Usuario.objects.create(
            nombre="Pedro",
            apellido="Lopez",
            edad=22,
            genero="M",
            email="pedro_acceso@gmail.com",
            password=make_password("Abc123!@")
        )
        self.usuario2.tipo_estudiante = 'U'
        self.usuario2.save()
        PerfilUniversitario.objects.create(
            usuario=self.usuario2,
            universidad="Universidad de los Andes",
            carrera="Medicina",
            creditos_para_graduarse=200,
            creditos_minimos_por_semestre=18,
            creditos_maximos_por_semestre=24,
            semestre_actual=1,
            creditos_aprobados=0,
            promedio_minimo_carrera=3.5
        )

        refresh2 = RefreshToken.for_user(self.usuario2)
        self.token_usuario2 = str(refresh2.access_token)

    def test_usuario2_no_puede_ver_semestres_de_usuario1(self):
        # Usuario 2 lista sus semestres — no debe ver los de usuario 1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario2}')
        response = self.client.get('/api/semestres/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s['id'] for s in response.data]
        self.assertNotIn(self.semestre1.id, ids)

    def test_usuario2_no_puede_eliminar_semestre_de_usuario1(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario2}')
        url = f'/api/semestres/{self.semestre1.id}/'
        response = self.client.delete(url)
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ])

    def test_usuario2_no_puede_editar_materia_de_usuario1(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario2}')
        url = f'/api/materias/{self.materia1.id}/'
        response = self.client.put(url, {
            'nombre': 'Hackeado',
            'creditos': 1,
            'total_notas': 1,
            'escala_notas': '5.0',
            'nota_minima_aprobacion': 3.0,
            'color': '#000000'
        }, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ])

    def test_usuario2_no_puede_ver_perfil_de_usuario1(self):
        # Cada usuario solo ve su propio perfil
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_usuario2}')
        response = self.client.get('/api/perfil-universitario/detalle/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['universidad'], 'Universidad Nacional')
