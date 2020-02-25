# Use an official Python runtime as a parent image
FROM python:3.6.4

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable or pass during run time like docker run --env "db_host=foo" --env "db_name=design_db"
# Build syntax docker build --build-arg db_host=127.0.0.1 --build-arg db_pass=foobar . -t foo
ARG db_host
ARG db_name
ARG db_user
ARG db_pass

ENV db_host=$db_host
ENV db_name=$db_name
ENV db_user=$db_user
ENV db_pass=$db_pass


# Run app.py when the container launches
# Run when deploying app for first time
#### Remove after db schema is created
#RUN python manage.py db init
#RUN python manage.py db migrate
RUN python manage.py db upgrade

CMD ["python", "runserver.py"]
