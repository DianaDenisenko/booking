# Description (Django REST API)

This application is an API for booking office workspaces. It allows users to register, authenticate, and book available office spaces.

# Running the Application

To run the application, follow these steps:

1. Build the Docker images using the command:
    ```
    docker-compose build
    ```

2. Start the containers in the background using the command:
    ```
    docker-compose up -d
    ```

3. Create a Django superuser by following these steps:
    - Access the terminal inside the container by running the command:
      ```
      docker-compose exec web bash
      ```
    - Then, execute the Django superuser creation command:
      ```
      python manage.py createsuperuser
      ```
    - Follow the prompts to create the superuser, including specifying a username, email address, and password.
