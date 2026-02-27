from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny # para dar persimo para que se logue el que quiera
from .serializers import RegistroUsuarioSerializer , LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken # genera los tokens JWT
from django.contrib.auth.hashers import check_password #compara la contraseña que llega con el hash guardado en la BD
from .models import Usuario

class RegistroView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroUsuarioSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()  # guarda y retorna el usuario
            refresh = RefreshToken.for_user(usuario)  # genera los tokens
            return Response({
                "mensaje": "Usuario registrado exitosamente",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# login
class LoginView(APIView):
    permission_classes = [AllowAny]# cualquier puede hacer login

    def post(self, request):
        serializer = LoginSerializer(data=request.data)# cone stoindicamso que estos son los datos que le usuario envia en formato json
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            try:
                usuario = Usuario.objects.get(email=email)
            except Usuario.DoesNotExist:
                return Response(
                    {"error": "Credenciales inválidas"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if not check_password(password, usuario.password):
                return Response(
                    {"error": "Credenciales inválidas"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            refresh = RefreshToken.for_user(usuario)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


