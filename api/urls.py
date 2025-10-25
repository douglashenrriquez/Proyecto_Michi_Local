from django.urls import path
from .views import hola
from .views import listar_jugadores, stats_jugador, crear_jugador, crear_partida, editar_jugador, ranking_jugadores, login_jugador
urlpatterns = [
    path('', hola, name='hola'),   # GET /
    path('jugadores/', listar_jugadores, name='listar_jugadores'),  # GET /jugadores/
    path('jugadores/<int:jugador_id>/stats/', stats_jugador, name='stats_jugador'),  # GET /jugadores/<id>/stats/
    path('jugadores/nuevo/', crear_jugador, name='crear_jugador'),
    path('partidas/nueva/', crear_partida, name='crear_partida'),
    path('jugadores/<int:jugador_id>/editar/', editar_jugador, name='editar_jugador'),
    path('ranking/', ranking_jugadores, name='ranking_jugadores'),
    path('login/', login_jugador, name='login_jugador'),
]