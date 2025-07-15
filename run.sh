#!/bin/bash
source venv/bin/activate
FLASK_APP=backend/app.py FLASK_ENV=development flask run

#para rodar >  ./run.sh