# Online Cinema API

A FastAPI-based online cinema platform that allows users to browse, purchase, and watch movies. The project implements a comprehensive backend system with user authentication, movie management, shopping cart functionality, and payment processing.

## Key Features

- **Movie Management**: 
  - Browse and search movies
  - Filter by year, rating, and price
  - Detailed movie information including directors, actors, and genres
  - Movie ratings and reviews

- **User System**:
  - Secure JWT-based authentication
  - Email verification for registration
  - Password reset functionality
  - User profile management

- **Shopping Features**:
  - Shopping cart functionality
  - Secure payment processing with Stripe
  - Order history
  - Email notifications for orders

- **Technical Features**:
  - Asynchronous API with FastAPI
  - Background task processing with Celery
  - PostgreSQL database with asyncpg
  - Comprehensive API documentation

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with asyncpg
- **Task Queue**: Celery
- **Container**: Docker & Docker Compose
- **Payment**: Stripe API
- **Authentication**: JWT (jose)
- **Testing**: pytest
- **Package Management**: Poetry


## Installation

### Prerequisites
- Python 3.11 or higher
- Docker and Docker Compose
- Poetry for dependency management

### Using Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd fast_api_online_cinema_project
```

2. Create a .env file in the project root:
```env
SECRET_KEY_ACCESS=your_access_secret_key
SECRET_KEY_REFRESH=your_refresh_secret_key
EMAIL_HOSTNAME=your_email_hostname
EMAIL_ADDRESS=your_email
EMAIL_PASSWORD=your_email_password
STRIPE_API_KEY=your_stripe_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
```

3. Build and start the containers:
```bash
docker-compose up -d
```

### Local Development

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables (see .env example above)

3. Start PostgreSQL and Redis (can be run via Docker):
```bash
docker-compose up -d postgres redis
```

4. Run the application:
```bash
poetry run uvicorn src.main:app --reload
```

## API Documentation

Once the application is running, you can access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc


## Testing

Run the test suite:
```bash
poetry run pytest
```

## Author

Mykyta Fedotov - [nikita.fedotov222@gmail.com](mailto:nikita.fedotov222@gmail.com)
