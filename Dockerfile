FROM python:3.7

RUN pip install fastapi uvicorn

EXPOSE 8000

COPY /api /api
COPY /data /data

RUN pip install -r /api/requirements.txt

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]