FROM python:3
EXPOSE 8000

WORKDIR /poc_farallon

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./api

ENTRYPOINT [ "python" ]
CMD ["api/app.py"]