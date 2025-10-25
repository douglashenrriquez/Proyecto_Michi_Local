from django.db import models

class Jugador(models.Model):
    id = models.AutoField(primary_key=True)
    nombre_usuario = models.CharField(max_length=100)
    contrasena = models.CharField(max_length=255)
    correo = models.CharField(max_length=100, null=True, blank=True)
    total_victorias = models.IntegerField(default=0)
    total_derrotas = models.IntegerField(default=0)
    partidas_jugadas = models.IntegerField(default=0)
    promedio_tiempo = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    nivel_mas_jugado = models.CharField(max_length=20, default="Básico")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'jugadores'

    def __str__(self):
        return self.nombre_usuario


class Partida(models.Model):
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, db_column='jugador_id')
    resultado = models.CharField(max_length=10)  # 'Victoria' o 'Derrota'
    tiempo = models.DecimalField(max_digits=5, decimal_places=2)
    nivel = models.CharField(max_length=20)      # 'Básico'|'Medio'|'Avanzado'
    fecha = models.DateTimeField()

    class Meta:
        db_table = 'partidas'
