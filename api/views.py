from django.http import JsonResponse
from .models import Jugador
from django.db import connection
from django.db.models import Count, Avg, Q
from .models import Partida, Jugador
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt
from .models import Partida, Jugador
from django.utils.dateparse import parse_datetime
from decimal import Decimal, InvalidOperation
from django.db.models import Q

def hola(request):
    db_ok = False
    error = None
    try:
        # Chequeo simple de conectividad
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
        db_ok = True
    except Exception as e:
        error = str(e)

    return JsonResponse({
        "message": "Hola mundo",
        "database": {
            "connected": db_ok,
            "error": error
        }
    })

def listar_jugadores(request):
    jugadores = list(Jugador.objects.values())
    return JsonResponse(jugadores, safe=False)

def stats_jugador(request, jugador_id):
    # Datos del jugador (id + nombre + correo)
    jugador = Jugador.objects.filter(id=jugador_id).values('id', 'nombre_usuario', 'correo').first()
    if not jugador:
        return JsonResponse({"error": "Jugador no encontrado"}, status=404)

    qs = Partida.objects.filter(jugador_id=jugador_id)

    agg = qs.aggregate(
        total_victorias=Count('id', filter=Q(resultado='Victoria')),
        total_derrotas=Count('id', filter=Q(resultado='Derrota')),
        partidas_jugadas=Count('id'),
        promedio_tiempo=Avg('tiempo'),
    )

    # Nivel más jugado (modo)
    nivel_row = qs.values('nivel').annotate(c=Count('*')).order_by('-c').first()
    nivel_mas_jugado = nivel_row['nivel'] if nivel_row else None

    # Normaliza nulos y decimales
    resp = {
        "jugador": jugador,
        "stats": {
            "total_victorias": agg['total_victorias'] or 0,
            "total_derrotas": agg['total_derrotas'] or 0,
            "partidas_jugadas": agg['partidas_jugadas'] or 0,
            "promedio_tiempo": float(agg['promedio_tiempo']) if agg['promedio_tiempo'] is not None else 0.0,
            "nivel_mas_jugado": nivel_mas_jugado
        }
    }
    return JsonResponse(resp)

@csrf_exempt
def crear_jugador(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body or '{}')
        nombre = data.get('nombre_usuario')
        contrasena = data.get('contrasena')
        correo = data.get('correo')

        # Validaciones básicas
        if not nombre or not contrasena or not correo:
            return JsonResponse({
                "error": "Los campos nombre_usuario, contrasena y correo son obligatorios"
            }, status=400)

        # Verificar duplicado de nombre o correo
        if Jugador.objects.filter(nombre_usuario=nombre).exists():
            return JsonResponse({"error": "El nombre de usuario ya existe"}, status=409)
        if Jugador.objects.filter(correo=correo).exists():
            return JsonResponse({"error": "El correo ya está registrado"}, status=409)

        # Crear jugador
        jugador = Jugador.objects.create(
            nombre_usuario=nombre,
            contrasena=contrasena,
            correo=correo,
            total_victorias=0,
            total_derrotas=0,
            partidas_jugadas=0,
            promedio_tiempo=0.00,
            nivel_mas_jugado="Básico",
            fecha_registro=timezone.now()
        )

        return JsonResponse({
            "mensaje": "Jugador creado correctamente",
            "jugador": {
                "id": jugador.id,
                "nombre_usuario": jugador.nombre_usuario,
                "correo": jugador.correo
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def _recompute_stats(jugador_id: int):
    qs = Partida.objects.filter(jugador_id=jugador_id)
    agg = qs.aggregate(
        total_victorias=Count('id', filter=Q(resultado='Victoria')),
        total_derrotas=Count('id', filter=Q(resultado='Derrota')),
        partidas_jugadas=Count('id'),
        promedio_tiempo=Avg('tiempo'),
    )
    nivel_row = qs.values('nivel').annotate(c=Count('*')).order_by('-c').first()
    nivel_mas_jugado = nivel_row['nivel'] if nivel_row else None

    # Guarda en la tabla jugadores
    Jugador.objects.filter(id=jugador_id).update(
        total_victorias=agg['total_victorias'] or 0,
        total_derrotas=agg['total_derrotas'] or 0,
        partidas_jugadas=agg['partidas_jugadas'] or 0,
        promedio_tiempo=(agg['promedio_tiempo'] or 0),
        nivel_mas_jugado=nivel_mas_jugado
    )
def _recompute_stats(jugador_id: int):
    qs = Partida.objects.filter(jugador_id=jugador_id)
    agg = qs.aggregate(
        total_victorias=Count('id', filter=Q(resultado='Victoria')),
        total_derrotas=Count('id', filter=Q(resultado='Derrota')),
        partidas_jugadas=Count('id'),
        promedio_tiempo=Avg('tiempo'),
    )
    nivel_row = qs.values('nivel').annotate(c=Count('*')).order_by('-c').first()
    nivel_mas_jugado = nivel_row['nivel'] if nivel_row else None

    Jugador.objects.filter(id=jugador_id).update(
        total_victorias=agg['total_victorias'] or 0,
        total_derrotas=agg['total_derrotas'] or 0,
        partidas_jugadas=agg['partidas_jugadas'] or 0,
        promedio_tiempo=(agg['promedio_tiempo'] or 0),
        nivel_mas_jugado=nivel_mas_jugado
    )

@csrf_exempt
def crear_partida(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body or '{}')

        jugador_id = data.get('jugador_id')
        resultado = data.get('resultado')        # 'Victoria' | 'Derrota'
        nivel = data.get('nivel')                # 'Básico' | 'Medio' | 'Avanzado'
        fecha_in = data.get('fecha')             
        tiempo_in = data.get('tiempo')           # número

        # Validaciones mínimas
        if not jugador_id:
            return JsonResponse({"error": "jugador_id es obligatorio"}, status=400)
        if resultado not in ('Victoria', 'Derrota'):
            return JsonResponse({"error": "resultado debe ser 'Victoria' o 'Derrota'"}, status=400)
        if nivel is None:
            return JsonResponse({"error": "nivel es obligatorio"}, status=400)
        try:
            tiempo = Decimal(str(tiempo_in))
        except (InvalidOperation, TypeError):
            return JsonResponse({"error": "tiempo debe ser numérico"}, status=400)

        # Normaliza fecha
        if fecha_in:
            dt = parse_datetime(fecha_in)
            if dt is None:
                return JsonResponse({"error": "fecha debe ser ISO8601. Ej: 2025-10-18T01:55:00"}, status=400)
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            fecha = dt
        else:
            fecha = timezone.now()

        # Verifica jugador
        if not Jugador.objects.filter(id=jugador_id).exists():
            return JsonResponse({"error": "Jugador no existe"}, status=404)

        # Crea la partida
        p = Partida.objects.create(
            jugador_id=jugador_id,
            resultado=resultado,
            tiempo=tiempo,
            nivel=nivel,
            fecha=fecha
        )

        # Recalcula agregados
        _recompute_stats(jugador_id)

        return JsonResponse({
            "mensaje": "Partida registrada",
            "partida": {
                "id": p.id,
                "jugador_id": p.jugador_id,
                "resultado": p.resultado,
                "tiempo": float(p.tiempo),
                "nivel": p.nivel,
                "fecha": p.fecha.isoformat()
            }
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

@csrf_exempt
def editar_jugador(request, jugador_id):
    if request.method not in ['PUT', 'PATCH']:
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body or '{}')

        nombre = data.get('nombre_usuario')
        contrasena = data.get('contrasena')
        correo = data.get('correo')

        jugador = Jugador.objects.filter(id=jugador_id).first()
        if not jugador:
            return JsonResponse({"error": "Jugador no encontrado"}, status=404)

        # Validar duplicados si cambian el nombre o correo
        if nombre and nombre != jugador.nombre_usuario and Jugador.objects.filter(nombre_usuario=nombre).exists():
            return JsonResponse({"error": "El nombre de usuario ya está en uso"}, status=409)
        if correo and correo != jugador.correo and Jugador.objects.filter(correo=correo).exists():
            return JsonResponse({"error": "El correo ya está registrado"}, status=409)

        # Actualizar solo los campos enviados
        if nombre is not None:
            jugador.nombre_usuario = nombre
        if contrasena is not None:
            jugador.contrasena = contrasena
        if correo is not None:
            jugador.correo = correo

        jugador.save()

        return JsonResponse({
            "mensaje": "Jugador actualizado correctamente",
            "jugador": {
                "id": jugador.id,
                "nombre_usuario": jugador.nombre_usuario,
                "contrasena": jugador.contrasena,
                "correo": jugador.correo
            }
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def ranking_jugadores(request):
    # Agrupa las partidas por jugador y cuenta solo las ganadas
    ranking = (
        Partida.objects
        .values('jugador__id', 'jugador__nombre_usuario')
        .annotate(
            partidas_ganadas=Count('id', filter=Q(resultado='Victoria')),
            partidas_jugadas=Count('id')
        )
        .order_by('-partidas_ganadas')
    )

    data = list(ranking)
    for i, jugador in enumerate(data, start=1):
        jugador["posicion"] = i
    return JsonResponse(data, safe=False)

@csrf_exempt
def login_jugador(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body or '{}')
        identificador = data.get('nombre_usuario')  # puede ser usuario o correo
        contrasena = data.get('contrasena')

        if not identificador or not contrasena:
            return JsonResponse({
                "error": "Debe ingresar nombre_usuario o correo y la contrasena"
            }, status=400)

        # Buscar por nombre_usuario o correo
        user = Jugador.objects.filter(
            Q(nombre_usuario=identificador) | Q(correo=identificador),
            contrasena=contrasena
        ).values('id', 'nombre_usuario', 'correo').first()

        if not user:
            return JsonResponse({
                "ok": False,
                "error": "Credenciales inválidas"
            }, status=401)

        # Login exitoso
        return JsonResponse({
            "ok": True,
            "usuario": {
                "id": user['id'],
                "nombre_usuario": user['nombre_usuario'],
                "correo": user['correo']
            }
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)