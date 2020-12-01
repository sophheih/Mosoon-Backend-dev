FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY . /code/
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]