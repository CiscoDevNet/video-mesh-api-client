# Set base image as python
FROM python:3.10.8

# Update and install dependencies
RUN apt update -y
RUN apt upgrade -y
RUN apt install vim python3-pip libpq-dev python3-dev -y && pip3 install --upgrade pip

# Setting up Flask app
COPY ../app/ app/
COPY ../setup/sql/ setup/sql/
COPY ../requirements.txt requirements.txt
RUN pip3 install --no-deps -r requirements.txt

# Run the app
CMD ["python3", "app/app.py"]