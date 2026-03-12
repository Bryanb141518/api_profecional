from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import (
    RegistroView,
    LoginView,
    LogoutView,
    TipoEstudianteView,
    PerfilUniversitarioView,
    PerfilUniversitarioDetailView,
    PerfilSecundariaView,
    SemestreView,
    SemestreDetailView,
    MateriaView,
    MateriaDetailView,
    NotaView,
    NotaDetailView,
    TareaView,
    TareaDetailView,
    ClaseHorarioView,
    ClaseHorarioDetailView,
)

urlpatterns = [

    # ── Auth
    path('registro/',       RegistroView.as_view(),      name='registro'),
    path('login/',          LoginView.as_view(),         name='login'),
    path('logout/',         LogoutView.as_view(),        name='logout'),
    path('token/refresh/',  TokenRefreshView.as_view(),  name='token_refresh'),

    # ── Usuario
    path('tipo-estudiante/', TipoEstudianteView.as_view(), name='tipo-estudiante'),

    # ── Perfil universitario
    # POST  → crear perfil
    path('perfil-universitario/',
         PerfilUniversitarioView.as_view(),
         name='perfil-universitario'),

    # GET / PUT / DELETE → ver, editar, eliminar perfil
    path('perfil-universitario/detalle/',
         PerfilUniversitarioDetailView.as_view(),
         name='perfil-universitario-detalle'),

    # ── Perfil secundaria
    # POST / GET
    path('perfil-secundaria/',
         PerfilSecundariaView.as_view(),
         name='perfil-secundaria'),

    # ── Semestres
    # GET (lista) / POST (crear)
    path('semestres/',
         SemestreView.as_view(),
         name='semestres'),

    # GET / PUT / DELETE (detalle)
    path('semestres/<int:semestre_id>/',
         SemestreDetailView.as_view(),
         name='semestre-detalle'),

    # ── Materias ───────────────────────────────────────
    # GET (lista del semestre) / POST (crear en semestre)
    path('semestres/<int:semestre_id>/materias/',
         MateriaView.as_view(),
         name='materias'),

    # GET / PUT / DELETE (detalle de materia)
    path('materias/<int:materia_id>/',
         MateriaDetailView.as_view(),
         name='materia-detalle'),

    # ── Notas / Actividades ────────────────────────────
    # GET (lista de la materia) / POST (crear en materia)
    path('materias/<int:materia_id>/notas/',
         NotaView.as_view(),
         name='notas'),

    # GET / PUT / DELETE (detalle de nota)
    path('notas/<int:nota_id>/',
         NotaDetailView.as_view(),
         name='nota-detalle'),

    # ── Tareas ─────────────────────────────────────────
    # GET (lista del semestre) / POST (crear en semestre)
    path('semestres/<int:semestre_id>/tareas/',
         TareaView.as_view(),
         name='tareas'),

    # GET / PUT / DELETE (detalle de tarea)
    path('tareas/<int:tarea_id>/',
         TareaDetailView.as_view(),
         name='tarea-detalle'),

    # ── Horario ────────────────────────────────────────
    # GET (todo el horario) / POST (agregar clase) / DELETE (limpiar todo)
    path('horario/',
         ClaseHorarioView.as_view(),
         name='horario'),

    # PUT / DELETE (editar o eliminar una clase específica)
    path('horario/<int:clase_id>/',
         ClaseHorarioDetailView.as_view(),
         name='horario-detalle'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
