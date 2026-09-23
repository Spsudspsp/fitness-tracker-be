# Fitness Tracker Backend

Django REST Framework backend for the fitness tracking application.

The backend provides the main REST API, handles authentication and persistent application data, and coordinates background tasks and communication with the AI service.

## Features

* User registration, authentication, and profiles
* Exercise management
* Workout management
* Membership management
* Notifications
* Training plan management
* Nutrition-related functionality
* AI training and nutrition plan integration
* Background task processing with Celery
* PostgreSQL persistence
* REST API for the React frontend

## Tech Stack

* Python
* Django
* Django REST Framework
* PostgreSQL
* Celery
* Redis
* Docker
* Docker Compose

## Architecture

```text
React Frontend
      |
      v
Django REST API
      |
      +---- PostgreSQL
      |
      +---- Redis
      |       |
      |       v
      |     Celery
      |
      +---- FastAPI AI Service
                |
                +-- OpenAI
                +-- Gemini
```

Django acts as the central application backend and source of truth for persistent data.

Celery is used for background operations such as AI plan generation, while Redis is used as the task broker.

The AI service runs separately and communicates with the backend over HTTP.

## Configuration

Create a `.env` file containing the required application configuration.

```bash
cp .env-example .env
```

Configure the required database, Django, Redis, and service settings before starting the application.

Do not commit secrets or production credentials to the repository.

## Running with Docker

Docker Compose is the recommended way to run the backend and its dependencies.

Before initial startup create a network "fitness-tracker-network". This network must exist before starting the service. Compose will not create it automatically:

```bash
docker network create fitness-tracker-network
```

Build and start the services:

```bash
docker compose up --build
```

Start without rebuilding:

```bash
docker compose up
```

Run in the background:

```bash
docker compose up -d
```

Stop the services:

```bash
docker compose down
```

After the initial startup, load the exercise data:

```bash
docker compose exec backend python manage.py load_exercises
```

The Docker environment runs the main application services, including:

* Django backend
* PostgreSQL
* Redis
* Celery worker

## Running Locally

Running the backend outside Docker requires PostgreSQL and Redis to be available separately.

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply database migrations:

```bash
python manage.py migrate
```

Load initial exercises data:

```bash
python manage.py load_exercises
```

Start the Django development server:

```bash
python manage.py runserver
```

Start a Celery worker separately.

## API

The application exposes REST endpoints for frontend and service communication.

User-related endpoints are available under:

```text
/users/
```

Additional endpoints handle exercises, workouts, training plans, nutrition, and other application functionality.

## AI Service Integration

AI generation is handled by a separate FastAPI service.

The backend:

1. Collects and validates application data.
2. Queues generation tasks through Celery.
3. Sends the required data to the AI service.
4. Receives structured generated plans.
5. Converts and stores the result as application data.

The AI service does not access the PostgreSQL database directly.

## Project Structure

The project is split into Django applications responsible for different parts of the fitness tracker.

## Related Components

The complete application consists of:

* React frontend
* Django REST Framework backend
* PostgreSQL
* Celery
* Redis
* FastAPI AI service
