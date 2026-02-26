from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse


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