#!/bin/bash
source /home/www/fastapi_worker/.env/bin/activate
uvicorn main_sql:app --port 8002 --workers 5 --app-dir /home/www/fastapi_worker/
