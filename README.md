# Football Predictor - Django Skeleton

Estructura mínima para arrancar una app Django que sincroniza partidos y calcula pronósticos.

## Contenido
- manage.py
- requirements.txt
- config/ (settings, urls, wsgi)
- predictor/ (app: models, views, urls, templates, utils, management command)
- templates/predictor/dashboard.html

## Uso rápido (entorno Linux / WSL / Mac):
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd football_predictor_skeleton
export DJANGO_SETTINGS_MODULE=config.settings
python manage.py migrate
# configurar FOOTBALL_API_KEY en config/settings.py o en env
python manage.py fetch_matches
python manage.py runserver
```
