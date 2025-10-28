from django.core.management.base import BaseCommand
from django.conf import settings
from predictor.models import Match, Team
import requests
import math
import random
from datetime import date
from datetime import date, timedelta

class Command(BaseCommand):
    help = "Trae próximos partidos, calcula probabilidades y resultado más probable (versión mejorada con Poisson ajustado y fuerza ofensiva/defensiva)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--liga',
            type=str,
            required=True,
            help='Código de la liga a consultar (ejemplo: PL, PD, SA, BL1, FL1, CL, etc.)'
        )

    # --- Cache local para evitar múltiples llamadas repetidas ---
    historicos_cache = {}

    # --- Función Poisson ---
    def poisson_prob(self, k, lam):
        return (lam ** k * math.exp(-lam)) / math.factorial(k)

    # --- Cálculo de probabilidades 1X2 ---
    def calcular_probabilidades(self, lambda_home, lambda_away, max_goles=6):
        prob_local = prob_empate = prob_visitante = 0
        distribucion = {}

        for i in range(0, max_goles + 1):
            for j in range(0, max_goles + 1):
                p = self.poisson_prob(i, lambda_home) * self.poisson_prob(j, lambda_away)
                distribucion[(i, j)] = p
                if i > j:
                    prob_local += p
                elif i == j:
                    prob_empate += p
                else:
                    prob_visitante += p

        total = prob_local + prob_empate + prob_visitante
        if total == 0:
            return 0.33, 0.33, 0.33, (1, 1)

        prob_local /= total
        prob_empate /= total
        prob_visitante /= total

        # Resultado más probable (score con mayor probabilidad)
        most_likely_score = max(distribucion.items(), key=lambda x: x[1])[0]

        return round(prob_local, 2), round(prob_empate, 2), round(prob_visitante, 2), most_likely_score

    # --- Obtener promedios de goles históricos ---
    def obtener_goles_historicos(self, team_id):
        if team_id in self.historicos_cache:
            return self.historicos_cache[team_id]

        api_key = settings.FOOTBALL_API_KEY
        url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=80"
        headers = {"X-Auth-Token": api_key}
        response = requests.get(url, headers=headers)

        # Si falla la API, devolvemos valores estándar
        if response.status_code != 200:
            valores = (1.5, 1.1, 1.3, 1.2)
            self.historicos_cache[team_id] = valores
            return valores

        data = response.json()
        partidos = data.get("matches", [])
        if not partidos:
            valores = (1.4, 1.0, 1.2, 1.1)
            self.historicos_cache[team_id] = valores
            return valores

        goles_local_favor = goles_local_contra = 0
        goles_visit_favor = goles_visit_contra = 0
        count_local = count_visit = 0

        for m in partidos:
            home_id = m["homeTeam"]["id"]
            away_id = m["awayTeam"]["id"]
            home_score = m["score"]["fullTime"].get("home") or 0
            away_score = m["score"]["fullTime"].get("away") or 0

            if home_id == team_id:
                goles_local_favor += home_score
                goles_local_contra += away_score
                count_local += 1
            elif away_id == team_id:
                goles_visit_favor += away_score
                goles_visit_contra += home_score
                count_visit += 1

        prom_local_favor = goles_local_favor / count_local if count_local else 1.4
        prom_local_contra = goles_local_contra / count_local if count_local else 1.0
        prom_visit_favor = goles_visit_favor / count_visit if count_visit else 1.2
        prom_visit_contra = goles_visit_contra / count_visit if count_visit else 1.1

        resultado = (prom_local_favor, prom_local_contra, prom_visit_favor, prom_visit_contra)
        self.historicos_cache[team_id] = resultado
        return resultado

    # --- Lógica principal ---
    def handle(self, *args, **kwargs):
        liga = kwargs['liga'].upper()
        api_key = settings.FOOTBALL_API_KEY

        if not api_key:
            self.stdout.write(self.style.ERROR("❌ No se encontró FOOTBALL_API_KEY en settings.py"))
            return

        self.stdout.write(self.style.SUCCESS(f"🔑 Usando API Key: {api_key[:6]}..."))
        self.stdout.write(f"🌍 Consultando partidos de la liga: {liga}")

        # --- Rango de fechas ---

        # Fecha de inicio (hoy)
        inicio = date.today()

        #Fecha final (dentro de 7 días)
        fin = inicio + timedelta(days=7)
        date_from = inicio.isoformat()
        date_to = fin.isoformat()

        url = (
            f"https://api.football-data.org/v4/competitions/{liga}/matches"
            f"?dateFrom={date_from}&dateTo={date_to}"
             )


        # url = (
        #     f"https://api.football-data.org/v4/competitions/{liga}/matches"
        #     f"?dateFrom={date.today()}&dateTo=2025-12-25"
        # )
        headers = {"X-Auth-Token": api_key}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f"❌ Error en la petición: {response.status_code}"))
            return

        data = response.json()
        matches = data.get("matches", [])
        self.stdout.write(self.style.SUCCESS(f"✅ Partidos recibidos: {len(matches)}"))

        if not matches:
            self.stdout.write("⚠️ No hay partidos futuros disponibles o la liga no está incluida en la API Free.")
            return

        count_saved = 0
        media_goles_liga = 1.45  # promedio de goles por equipo por partido

        for match in matches:
            try:
                if match["status"] not in ["SCHEDULED", "TIMED"]:
                    continue

                home_team_data = match["homeTeam"]
                away_team_data = match["awayTeam"]

                home_team, _ = Team.objects.get_or_create(
                    api_id=home_team_data["id"],
                    defaults={"name": home_team_data["name"]}
                )
                away_team, _ = Team.objects.get_or_create(
                    api_id=away_team_data["id"],
                    defaults={"name": away_team_data["name"]}
                )

                # --- Promedios históricos ---
                (home_fav_local, home_contra_local, home_fav_visit, home_contra_visit) = \
                    self.obtener_goles_historicos(home_team.api_id)
                (away_fav_local, away_contra_local, away_fav_visit, away_contra_visit) = \
                    self.obtener_goles_historicos(away_team.api_id)

                # --- Índices de fuerza ofensiva y defensiva ---
                fuerza_ofensiva_home = home_fav_local / media_goles_liga
                fuerza_defensiva_away = away_contra_visit / media_goles_liga
                fuerza_ofensiva_away = away_fav_visit / media_goles_liga
                fuerza_defensiva_home = home_contra_local / media_goles_liga

                # --- Cálculo Poisson ajustado ---
                lambda_home = max(0.4, media_goles_liga * fuerza_ofensiva_home / max(fuerza_defensiva_away, 0.4))
                lambda_away = max(0.4, media_goles_liga * fuerza_ofensiva_away / max(fuerza_defensiva_home, 0.4))

                # Añadimos variabilidad para evitar resultados idénticos
                lambda_home *= 1 + random.uniform(-0.15, 0.15)
                lambda_away *= 1 + random.uniform(-0.15, 0.15)

                # Límites razonables
                lambda_home = min(max(lambda_home, 0.4), 3.5)
                lambda_away = min(max(lambda_away, 0.4), 3.5)

                # --- Calcular probabilidades ---
                prob_home, prob_draw, prob_away, score = self.calcular_probabilidades(lambda_home, lambda_away)

                # --- Guardar o actualizar partido ---
                Match.objects.update_or_create(
                    api_id=match["id"],
                    defaults={
                        "competition": match.get("competition", {}).get("name", "N/A"),
                        "date": match["utcDate"],
                        "status": match["status"],
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_score": match["score"]["fullTime"].get("home"),
                        "away_score": match["score"]["fullTime"].get("away"),
                        "prob_home_win": prob_home,
                        "prob_draw": prob_draw,
                        "prob_away_win": prob_away,
                        "most_likely_home_score": score[0],
                        "most_likely_away_score": score[1],
                    }
                )

                count_saved += 1
                self.stdout.write(
                    f"🏟️ {home_team.name} ({lambda_home:.2f}) vs {away_team.name} ({lambda_away:.2f}) "
                    f"-> {prob_home}-{prob_draw}-{prob_away} => {score[0]}-{score[1]}"
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"⚠️ Error guardando partido: {e}"))


        self.stdout.write(self.style.SUCCESS(f"💾 Partidos guardados o actualizados: {count_saved}"))
