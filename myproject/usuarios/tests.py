from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from .models import Usuario
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import ValidationError
from .models import PerfilUniversitario, PerfilSecundaria
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
        # Crear usuario para las pruebas
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
            total_semestres=10,
            semestre_actual=5,
            creditos_para_graduarse=160,
            creditos_aprobados=80
        )

        self.assertEqual(perfil.semestre_actual, 5)

    def test_semestre_mayor_que_total(self):
        perfil = PerfilUniversitario(
            usuario=self.usuario,
            universidad="Universidad Nacional",
            carrera="Ingeniería",
            total_semestres=8,
            semestre_actual=10,
            creditos_para_graduarse=160,
            creditos_aprobados=80
        )

        with self.assertRaises(ValidationError):
            perfil.full_clean()

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