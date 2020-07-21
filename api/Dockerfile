FROM python:3
EXPOSE 8000

COPY . /poc_farallon/api
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /poc_farallon


ENTRYPOINT [ "python" ]
CMD ["api/app.py"]