from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    Usuario, PerfilUniversitario, Semestre,
    Materia, Nota, Tarea, ClaseHorario
)
from .serializers import (
    RegistroUsuarioSerializer, LoginSerializer,
    TipoEstudianteSerializer, PerfilUniversitarioSerializer,
    PerfilSecundariaSerializer, SemestreSerializer,
    MateriaSerializer, NotaSerializer, TareaSerializer,
    ClaseHorarioSerializer
)

logger         = logging.getLogger('usuarios')
MAX_INTENTOS   = 5
TIEMPO_BLOQUEO = 30  # minutos

# AUTH

class RegistroView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroUsuarioSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            logger.info(f"Nuevo usuario registrado: {usuario.email}")
            refresh = RefreshToken.for_user(usuario)
            return Response({
                "mensaje": "Usuario registrado exitosamente",
                "refresh": str(refresh),
                "access":  str(refresh.access_token),
                "usuario": {
                    "nombre":  usuario.nombre,
                    "apellido": usuario.apellido,
                    "email":   usuario.email,
                }
            }, status=status.HTTP_201_CREATED)

        logger.warning(f"Registro fallido: {request.data.get('email', '?')}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email    = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            logger.warning(f"Login fallido - email no existe: {email}")
            return Response({"error": "Credenciales inválidas"},
                            status=status.HTTP_401_UNAUTHORIZED)

        # Verificar bloqueo
        if usuario.bloqueado_hasta and usuario.bloqueado_hasta > timezone.now():
            minutos = int((usuario.bloqueado_hasta - timezone.now()).seconds / 60)
            return Response(
                {"error": f"Cuenta bloqueada. Intenta en {minutos} minutos"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not check_password(password, usuario.password):
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= MAX_INTENTOS:
                usuario.bloqueado_hasta = timezone.now() + timedelta(minutes=TIEMPO_BLOQUEO)
                usuario.save()
                return Response(
                    {"error": f"Cuenta bloqueada por {TIEMPO_BLOQUEO} minutos"},
                    status=status.HTTP_403_FORBIDDEN
                )
            usuario.save()
            return Response({"error": "Credenciales inválidas"},
                            status=status.HTTP_401_UNAUTHORIZED)

        # Login exitoso
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta   = None
        usuario.save()

        refresh = RefreshToken.for_user(usuario)

        # Verificar si tiene perfil
        tiene_perfil_uni = hasattr(usuario, 'perfil_universitario')
        tiene_perfil_col = hasattr(usuario, 'perfil_secundaria')

        return Response({
            "refresh": str(refresh),
            "access":  str(refresh.access_token),
            "usuario": {
                "nombre":          usuario.nombre,
                "apellido":        usuario.apellido,
                "email":           usuario.email,
                "tipo_estudiante": usuario.tipo_estudiante,
                "tiene_perfil":    tiene_perfil_uni or tiene_perfil_col,
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "El refresh token es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            if int(token['user_id']) != int(request.user.id):
                return Response({"error": "Token no válido"},
                                status=status.HTTP_403_FORBIDDEN)
            token.blacklist()
            return Response({"mensaje": "Logout exitoso"},
                            status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# TIPO ESTUDIANTE

class TipoEstudianteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TipoEstudianteSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"mensaje": "Tipo de estudiante guardado exitosamente"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        return Response(
            {"tipo_estudiante": request.user.tipo_estudiante},
            status=status.HTTP_200_OK
        )

# PERFIL UNIVERSITARIO

class PerfilUniversitarioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PerfilUniversitarioSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"mensaje": "Perfil universitario creado exitosamente"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PerfilUniversitarioDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_perfil(self, request):
        try:
            return request.user.perfil_universitario
        except PerfilUniversitario.DoesNotExist:
            return None

    def get(self, request):
        perfil = self._get_perfil(request)
        if not perfil:
            return Response(
                {"error": "No tienes perfil universitario"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PerfilUniversitarioSerializer(
            perfil, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        perfil = self._get_perfil(request)
        if not perfil:
            return Response(
                {"error": "No tienes perfil universitario"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PerfilUniversitarioSerializer(
            perfil, data=request.data, partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"mensaje": "Perfil actualizado exitosamente"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        perfil = self._get_perfil(request)
        if not perfil:
            return Response(
                {"error": "No tienes perfil universitario"},
                status=status.HTTP_404_NOT_FOUND
            )
        perfil.delete()
        return Response(
            {"mensaje": "Perfil eliminado exitosamente"},
            status=status.HTTP_204_NO_CONTENT
        )

# PERFIL SECUNDARIA


class PerfilSecundariaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PerfilSecundariaSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(usuario=request.user)
            return Response(
                {"mensaje": "Perfil de secundaria creado exitosamente"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        try:
            perfil = request.user.perfil_secundaria
        except Exception:
            return Response(
                {"error": "No tienes perfil de secundaria"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PerfilSecundariaSerializer(perfil)
        return Response(serializer.data, status=status.HTTP_200_OK)
# SEMESTRE


class SemestreView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_perfil(self, request):
        try:
            return request.user.perfil_universitario
        except PerfilUniversitario.DoesNotExist:
            return None

    def get(self, request):
        perfil = self._get_perfil(request)
        if not perfil:
            return Response({"error": "No tienes perfil universitario"},
                            status=status.HTTP_404_NOT_FOUND)
        semestres  = Semestre.objects.filter(perfil=perfil)
        serializer = SemestreSerializer(semestres, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        perfil = self._get_perfil(request)
        if not perfil:
            return Response({"error": "No tienes perfil universitario"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = SemestreSerializer(
            data=request.data, context={'perfil': perfil}
        )
        if serializer.is_valid():
            serializer.save(perfil=perfil)
            return Response(
                {"mensaje": "Semestre creado exitosamente", "semestre": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SemestreDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_semestre(self, request, semestre_id):
        try:
            return Semestre.objects.get(
                id=semestre_id,
                perfil=request.user.perfil_universitario
            )
        except (Semestre.DoesNotExist, PerfilUniversitario.DoesNotExist):
            return None

    def get(self, request, semestre_id):
        semestre = self._get_semestre(request, semestre_id)
        if not semestre:
            return Response({"error": "Semestre no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = SemestreSerializer(semestre)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, semestre_id):
        semestre = self._get_semestre(request, semestre_id)
        if not semestre:
            return Response({"error": "Semestre no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = SemestreSerializer(
            semestre, data=request.data, partial=True,
            context={'perfil': semestre.perfil}
        )
        if serializer.is_valid():
            serializer.save()
            # Si el semestre se marca como completado, actualizar semestre_actual del perfil
            if request.data.get('estado') == 'completado':
                perfil = semestre.perfil
                if perfil.semestre_actual == semestre.numero:
                    perfil.semestre_actual += 1
                    perfil.save()
            return Response(
                {"mensaje": "Semestre actualizado", "semestre": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, semestre_id):
        semestre = self._get_semestre(request, semestre_id)
        if not semestre:
            return Response({"error": "Semestre no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)
        semestre.delete()
        return Response({"mensaje": "Semestre eliminado"},
                        status=status.HTTP_204_NO_CONTENT)

# MATERIA


class MateriaView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_semestre(self, request, semestre_id):
        try:
            return Semestre.objects.get(
                id=semestre_id,
                perfil=request.user.perfil_universitario
            )
        except (Semestre.DoesNotExist, PerfilUniversitario.DoesNotExist):
            return None

    def get(self, request, semestre_id):
        semestre = self._get_semestre(request, semestre_id)
        if not semestre:
            return Response({"error": "Semestre no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)
        materias   = Materia.objects.filter(semestre=semestre)
        serializer = MateriaSerializer(materias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, semestre_id):
        semestre = self._get_semestre(request, semestre_id)
        if not semestre:
            return Response({"error": "Semestre no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)

        # Verificar límite de créditos del semestre
        perfil          = request.user.perfil_universitario
        creditos_actuales = sum(
            m.creditos for m in semestre.materias.all()
        )
        creditos_nuevos = request.data.get('creditos', 0)
        if creditos_actuales + int(creditos_nuevos) > perfil.creditos_maximos_por_semestre:
            return Response(
                {"error": f"Superarías el máximo de {perfil.creditos_maximos_por_semestre} créditos por semestre"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MateriaSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(semestre=semestre)
            return Response(
                {"mensaje": "Materia creada exitosamente", "materia": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MateriaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_materia(self, request, materia_id):
        try:
            return Materia.objects.get(
                id=materia_id,
                semestre__perfil=request.user.perfil_universitario
            )
        except (Materia.DoesNotExist, PerfilUniversitario.DoesNotExist):
            return None

    def get(self, request, materia_id):
        materia = self._get_materia(request, materia_id)
        if not materia:
            return Response({"error": "Materia no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = MateriaSerializer(materia)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, materia_id):
        materia = self._get_materia(request, materia_id)
        if not materia:
            return Response({"error": "Materia no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = MateriaSerializer(
            materia, data=request.data, partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"mensaje": "Materia actualizada", "materia": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, materia_id):
        materia = self._get_materia(request, materia_id)
        if not materia:
            return Response({"error": "Materia no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)

        # Al eliminar materia perdida o activa, restar créditos si era aprobada
        if materia.estado == 'aprobada':
            perfil = request.user.perfil_universitario
            perfil.creditos_aprobados = max(
                0, perfil.creditos_aprobados - materia.creditos
            )
            perfil.save()

        materia.delete()
        return Response({"mensaje": "Materia eliminada"},
                        status=status.HTTP_204_NO_CONTENT)

# NOTA


class NotaView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_materia(self, request, materia_id):
        try:
            return Materia.objects.get(
                id=materia_id,
                semestre__perfil=request.user.perfil_universitario
            )
        except (Materia.DoesNotExist, PerfilUniversitario.DoesNotExist):
            return None

    def get(self, request, materia_id):
        materia = self._get_materia(request, materia_id)
        if not materia:
            return Response({"error": "Materia no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        notas      = Nota.objects.filter(materia=materia)
        serializer = NotaSerializer(notas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, materia_id):
        materia = self._get_materia(request, materia_id)
        if not materia:
            return Response({"error": "Materia no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = NotaSerializer(
            data=request.data, context={'materia': materia}
        )
        if serializer.is_valid():
            nota = serializer.save(materia=materia)
            # Recalcular estado de la materia
            self._recalcular_estado_materia(materia)
            return Response(
                {"mensaje": "Nota creada exitosamente", "nota": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _recalcular_estado_materia(self, materia):
        """Recalcula si la materia está aprobada o perdida y actualiza créditos."""
        notas_con_valor = materia.notas.filter(valor_obtenido__isnull=False)
        total_notas     = materia.total_notas

        if notas_con_valor.count() < total_notas:
            return  # Aún faltan notas

        # Calcular promedio ponderado
        total_pct     = sum(float(n.porcentaje) for n in notas_con_valor)
        if total_pct == 0:
            return

        promedio = sum(
            float(n.valor_obtenido) * float(n.porcentaje)
            for n in notas_con_valor
        ) / total_pct

        perfil          = materia.semestre.perfil
        estado_anterior = materia.estado

        if promedio >= float(materia.nota_minima_aprobacion):
            materia.estado = 'aprobada'
            if estado_anterior != 'aprobada':
                perfil.creditos_aprobados += materia.creditos
                perfil.save()
        else:
            materia.estado = 'perdida'
            if estado_anterior == 'aprobada':
                perfil.creditos_aprobados = max(
                    0, perfil.creditos_aprobados - materia.creditos
                )
                perfil.save()

        materia.save()


class NotaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_nota(self, request, nota_id):
        try:
            return Nota.objects.get(
                id=nota_id,
                materia__semestre__perfil=request.user.perfil_universitario
            )
        except (Nota.DoesNotExist, PerfilUniversitario.DoesNotExist):
            return None

    def get(self, request, nota_id):
        nota = self._get_nota(request, nota_id)
        if not nota:
            return Response({"error": "Nota no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(NotaSerializer(nota).data, status=status.HTTP_200_OK)

    def put(self, request, nota_id):
        nota = self._get_nota(request, nota_id)
        if not nota:
            return Response({"error": "Nota no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = NotaSerializer(
            nota, data=request.data, partial=True,
            context={'materia': nota.materia}
        )
        if serializer.is_valid():
            serializer.save()
            # Recalcular estado de la materia
            NotaView()._recalcular_estado_materia(nota.materia)
            return Response(
                {"mensaje": "Nota actualizada", "nota": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, nota_id):
        nota    = self._get_nota(request, nota_id)
        if not nota:
            return Response({"error": "Nota no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        materia = nota.materia
        nota.delete()
        # Recalcular estado
        materia.estado = 'activa'
        materia.save()
        NotaView()._recalcular_estado_materia(materia)
        return Response({"mensaje": "Nota eliminada"},
                        status=status.HTTP_204_NO_CONTENT)

# TAREA


class TareaView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_semestre(self, request, semestre_id):
        try:
            return Semestre.objects.get(
                id=semestre_id,
                perfil=request.user.perfil_universitario
            )
        except (Semestre.DoesNotExist, PerfilUniversitario.DoesNotExist):
            return None

    def get(self, request, semestre_id):
        semestre = self._get_semestre(request, semestre_id)
        if not semestre:
            return Response({"error": "Semestre no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)
        tareas     = Tarea.objects.filter(semestre=semestre)
        serializer = TareaSerializer(tareas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, semestre_id):
        semestre = self._get_semestre(request, semestre_id)
        if not semestre:
            return Response({"error": "Semestre no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = TareaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(semestre=semestre)
            return Response(
                {"mensaje": "Tarea creada exitosamente", "tarea": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TareaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_tarea(self, request, tarea_id):
        try:
            return Tarea.objects.get(
                id=tarea_id,
                semestre__perfil=request.user.perfil_universitario
            )
        except (Tarea.DoesNotExist, PerfilUniversitario.DoesNotExist):
            return None

    def get(self, request, tarea_id):
        tarea = self._get_tarea(request, tarea_id)
        if not tarea:
            return Response({"error": "Tarea no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(TareaSerializer(tarea).data, status=status.HTTP_200_OK)

    def put(self, request, tarea_id):
        tarea = self._get_tarea(request, tarea_id)
        if not tarea:
            return Response({"error": "Tarea no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = TareaSerializer(tarea, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"mensaje": "Tarea actualizada", "tarea": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, tarea_id):
        tarea = self._get_tarea(request, tarea_id)
        if not tarea:
            return Response({"error": "Tarea no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        tarea.delete()
        return Response({"mensaje": "Tarea eliminada"},
                        status=status.HTTP_204_NO_CONTENT)
# HORARIO

class ClaseHorarioView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_perfil(self, request):
        try:
            return request.user.perfil_universitario
        except PerfilUniversitario.DoesNotExist:
            return None

    def get(self, request):
        perfil = self._get_perfil(request)
        if not perfil:
            return Response({"error": "No tienes perfil universitario"},
                            status=status.HTTP_404_NOT_FOUND)
        clases     = ClaseHorario.objects.filter(perfil=perfil)
        serializer = ClaseHorarioSerializer(clases, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        perfil = self._get_perfil(request)
        if not perfil:
            return Response({"error": "No tienes perfil universitario"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = ClaseHorarioSerializer(
            data=request.data, context={'perfil': perfil}
        )
        if serializer.is_valid():
            serializer.save(perfil=perfil)
            return Response(
                {"mensaje": "Clase agregada al horario", "clase": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Limpiar todo el horario"""
        perfil = self._get_perfil(request)
        if not perfil:
            return Response({"error": "No tienes perfil universitario"},
                            status=status.HTTP_404_NOT_FOUND)
        ClaseHorario.objects.filter(perfil=perfil).delete()
        return Response({"mensaje": "Horario limpiado"},
                        status=status.HTTP_204_NO_CONTENT)


class ClaseHorarioDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_clase(self, request, clase_id):
        try:
            return ClaseHorario.objects.get(
                id=clase_id,
                perfil=request.user.perfil_universitario
            )
        except (ClaseHorario.DoesNotExist, PerfilUniversitario.DoesNotExist):
            return None

    def put(self, request, clase_id):
        clase = self._get_clase(request, clase_id)
        if not clase:
            return Response({"error": "Clase no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = ClaseHorarioSerializer(
            clase, data=request.data, partial=True,
            context={'perfil': clase.perfil}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"mensaje": "Clase actualizada", "clase": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, clase_id):
        clase = self._get_clase(request, clase_id)
        if not clase:
            return Response({"error": "Clase no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)
        clase.delete()
        return Response({"mensaje": "Clase eliminada"},
                        status=status.HTTP_204_NO_CONTENT)