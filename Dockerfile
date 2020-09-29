FROM python:3.8
WORKDIR /app
RUN pip install numpy==1.19.*
RUN pip install fastapi[all]==0.61.*
COPY . .
CMD python server_run.py