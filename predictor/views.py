import subprocess
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from predictor.models import Match
from datetime import timedelta
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login
from .forms import CustomLoginForm
from django.contrib import messages

# --- Dashboard principal ---
def dashboard(request):
    ligas = {
        "CL": {"nombre": "UEFA Champions League", "pais": "eu"},  # Unión Europea
        "PL": {"nombre": "Premier League", "pais": "gb"},
        "PD": {"nombre": "La Liga", "pais": "es"},
        "SA": {"nombre": "Serie A", "pais": "it"},
        "BL1": {"nombre": "Bundesliga", "pais": "de"},
        "FL1": {"nombre": "Ligue 1", "pais": "fr"},
        "BSA": {"nombre": "Brasileirão", "pais": "br"},
        "PPL": {"nombre": "Primeira Liga", "pais": "pt"},
        "DED": {"nombre": "Eredivisie", "pais": "nl"},
        "ELC": {"nombre": "Championship", "pais": "gb"},
        "WC": {"nombre": "FIFA World Cup", "pais": "fifa"},
    }

    # Cargar partidos (por defecto los futuros)
    upcoming = Match.objects.filter(date__gte=timezone.now()).order_by("date")[:100]
    items = procesar_partidos(upcoming) 
    total_partidos = len(items)
    context = {
        "ligas": ligas,
        "items": procesar_partidos(upcoming),
        "total_partidos": total_partidos,
        "current_time": timezone.now(),
    }
    return render(request, "predictor/dashboard.html", context)


# --- API para actualizar dinámicamente ---
def actualizar_liga(request):
    """Actualiza los datos de una liga y devuelve JSON para AJAX."""
    liga = request.POST.get("liga")

    if not liga:
        return JsonResponse({"error": "No se seleccionó una liga."}, status=400)

    try:
        # Borrar partidos anteriores
        Match.objects.all().delete()

        # Ejecutar el comando Django
        comando = f"python manage.py fetch_matches --liga={liga}"
        subprocess.run(comando, shell=True, check=True)

        # Filtrar próximos 7 días
        hoy = timezone.now()
        fecha_limite = hoy + timedelta(days=7)
        upcoming = Match.objects.filter(
            date__gte=hoy,
            date__lte=fecha_limite
        ).order_by("date")

        # Renderizar tabla
        data_html = render_tabla_html(upcoming)
        total_partidos = upcoming.count()

        return JsonResponse({
            "success": True,
            "html": data_html,
            "total_partidos": total_partidos
        })
    except subprocess.CalledProcessError:
        return JsonResponse({"error": "Error al obtener datos desde la API."}, status=500)


# --- Función auxiliar para procesar partidos ---
def procesar_partidos(queryset):
    matches_with_probs = []
    for m in queryset:
        prob_home = m.prob_home_win or 0
        prob_draw = m.prob_draw or 0
        prob_away = m.prob_away_win or 0

        max_prob = max(prob_home, prob_draw, prob_away)
        matches_with_probs.append({
            "match": m,
            "probs": {
                "home_win": prob_home,
                "draw": prob_draw,
                "away_win": prob_away,
                "most_likely_score": (
                    m.most_likely_home_score or 0,
                    m.most_likely_away_score or 0,
                ),
            },
            "classes": {
                "home_class": "prob-fav" if prob_home == max_prob else "",
                "draw_class": "prob-draw" if prob_draw == max_prob else "",
                "away_class": "prob-away" if prob_away == max_prob else "",
            },
        })
    return matches_with_probs



def render_tabla_html(queryset):
    context = {"items": procesar_partidos(queryset)}
    return render_to_string("predictor/tabla_partidos.html", context)

def login_view(request):
    if request.method == "POST":
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenido {user.username} ⚽ ¡Listo para apostar!")
                return redirect("dashboard")  
            else:
                messages.error(request, "Usuario o contraseña incorrectos")
        else:
            messages.error(request, "Error en el formulario")
    else:
        form = CustomLoginForm()
    return render(request, "predictor/login.html", {"form": form})