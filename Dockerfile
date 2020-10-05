FROM python:3.8
WORKDIR /app
RUN pip install numpy==1.18.* nltk==3.5.* fastapi[all]==0.61.* python-dotenv==0.14.* pymongo==3.11.* 

COPY . .
CMD python server_run.py