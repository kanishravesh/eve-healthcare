# EVE Healthcare Backend

A small Flask backend service for diagnostic test bookings and simulated payments.

## Features

- User signup and login
- JWT-based authentication
- Password hashing using bcrypt
- Diagnostic centres and available tests
- Authenticated diagnostic test bookings
- Simulated SUCCESS and FAILED payments
- Payment webhook handling
- Webhook idempotency
- Booking cancellation
- Swagger API documentation
- Application logging
- Automated API tests

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- PostgreSQL
- JWT
- bcrypt
- Flasgger
- pytest
- HTML, CSS and JavaScript for the frontend

## Project Structure

```text
evhealth/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── style.css
│       └── app.js
│
├── tests/
│   ├── __init__.py
│   └── test_api.py
│
├── logs/
│
├── seed.py
├── run.py
├── requirements.txt
├── README.md
└── .gitignore
```

> `.env` is intentionally not included in the repository because it contains local configuration and secrets.

## Setup

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd evhealth
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

For Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the PostgreSQL database

Create a PostgreSQL database named:

```text
eve_healthcare
```

For example:

```bash
createdb eve_healthcare
```

### 5. Create the `.env` file

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://username@localhost:5432/eve_healthcare
JWT_SECRET=your-secret-key
```

Replace `username` with your PostgreSQL username.

### 6. Start the application

```bash
python run.py
```

The application will run at:

```text
http://127.0.0.1:5000
```

### 7. Add sample data

In another terminal, run:

```bash
python seed.py
```

This adds sample diagnostic centres and tests.

## Frontend

The simple frontend is available at:

http://127.0.0.1:5000/app

It allows users to:

- View diagnostic centres
- View available tests
- Sign up
- Login
- Create bookings
- View their bookings
- Make simulated payments

## API Documentation

Swagger documentation is available at:

http://127.0.0.1:5000/apidocs/

Swagger can be used to view and test the API endpoints.

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/signup` | Register a new user |
| POST | `/login` | Login and receive JWT |
| GET | `/me` | Get the logged-in user |

### Centres and Tests

| Method | Endpoint | Description |
|---|---|---|
| GET | `/centres` | Get all diagnostic centres |
| GET | `/centres/<centre_id>/tests` | Get tests available at a centre |

### Bookings

| Method | Endpoint | Description |
|---|---|---|
| POST | `/bookings` | Create a booking |
| GET | `/bookings` | Get the logged-in user's bookings |
| GET | `/bookings/<booking_id>` | Get a specific booking |
| DELETE | `/bookings/<booking_id>` | Cancel a pending booking |

### Payments

| Method | Endpoint | Description |
|---|---|---|
| POST | `/payments` | Process a simulated payment |
| POST | `/payments/webhook` | Process a payment webhook |

## Authentication

After login, the API returns a JWT access token.

Protected endpoints require:

```text
Authorization: Bearer <access_token>
```

## Example Signup

Request:

```json
{
    "name": "Kanish",
    "email": "kanish@example.com",
    "password": "password123"
}
```

Example response:

```json
{
    "message": "User registered successfully",
    "user_id": 1
}
```

## Example Login

Request:

```json
{
    "email": "kanish@example.com",
    "password": "password123"
}
```

Example response:

```json
{
    "message": "Login successful",
    "access_token": "<JWT_TOKEN>"
}
```

## Example Booking

Request:

```json
{
    "test_id": 1,
    "centre_id": 1,
    "appointment_time": "2026-10-01T10:00:00"
}
```

A newly created booking starts with:

```text
PENDING
```

The booking amount is automatically taken from the selected test price.

## Example Successful Payment

Request:

```json
{
    "booking_id": 1,
    "status": "SUCCESS"
}
```

The booking status becomes:

```text
CONFIRMED
```

## Example Failed Payment

Request:

```json
{
    "booking_id": 1,
    "status": "FAILED"
}
```

The booking status becomes:

```text
FAILED
```

## Example Payment Webhook

Request:

```json
{
    "event_id": "event-123",
    "booking_id": 1,
    "status": "SUCCESS"
}
```

The webhook event ID is stored after processing.

If the same webhook is received again, the existing event is detected and another payment is not created.

## Database Design

The application uses PostgreSQL with the following main tables.

### User

Stores registered users.

```text
User
├── id
├── name
├── email
└── password
```

### Centre

Stores diagnostic centres.

```text
Centre
├── id
├── name
└── location
```

### Test

Stores tests offered by diagnostic centres.

```text
Test
├── id
├── name
├── price
└── centre_id
```

### Booking

Stores diagnostic test bookings.

```text
Booking
├── id
├── user_id
├── test_id
├── centre_id
├── appointment_time
├── amount
└── status
```

### Payment

Stores payment attempts.

```text
Payment
├── id
├── booking_id
├── amount
└── status
```

### WebhookEvent

Stores processed webhook event IDs.

```text
WebhookEvent
├── id
└── event_id
```

## Booking and Payment Flow

```text
User
 |
 v
Login
 |
 v
JWT Token
 |
 v
Select Centre
 |
 v
Select Test
 |
 v
Create Booking
 |
 v
PENDING
 |
 v
Payment
 |
 +---- SUCCESS ----> CONFIRMED
 |
 +---- FAILED -----> FAILED
```

### Payment Webhook Flow

```text
Payment Provider
       |
       v
POST /payments/webhook
       |
       v
Check event_id
       |
       +---- Already processed ---> Ignore
       |
       +---- New event -----------> Process payment
```

## Webhook Idempotency

Each webhook contains a unique `event_id`.

Before processing a webhook, the application checks whether that event has already been processed.

This prevents the same webhook from creating multiple payment records when the provider retries the same event.

## Authorization

Authenticated users can only access and modify their own bookings.

For example, a user cannot make a payment for another user's booking.

The payment endpoint verifies the booking owner using the JWT identity.

## Testing

The project contains automated API tests.

Run:

```bash
pytest
```

The tests use an isolated in-memory SQLite database.

This prevents tests from modifying or deleting the development PostgreSQL database.

The test suite covers:

- User signup
- User login
- Current user endpoint
- Booking creation
- Successful payment
- Failed payment
- Duplicate webhook handling
- Preventing one user from paying another user's booking

## Logging

Application logs are stored in:

```text
logs/app.log
```

Important events such as:

- User registration
- Login
- Booking creation
- Payment processing
- Webhook processing
- Duplicate webhook detection
- Booking cancellation

are logged using Python's built-in logging module.

The `logs/` directory is excluded from Git.

## Assumptions

- Payments are simulated and no real payment provider is connected.
- Webhook signature verification is not implemented because the payment provider is simulated.
- Appointment availability and time-slot conflict checking are outside the current scope.
- PostgreSQL is used as the main application database.
- Tests use an isolated SQLite database.
- JWT tokens are used for API authentication.
- The frontend is intended as a simple demonstration interface.

## Future Improvements

For a production version, the following could be added:

- Database migrations using Alembic
- Real payment-provider integration
- Webhook signature verification
- Stronger transaction handling for concurrent webhooks
- Decimal/Numeric types for monetary values
- Appointment slot availability checking
- Pagination
- Rate limiting
- Docker deployment
- Production-ready JWT storage and security configuration

## Running the Project

The basic commands are:

```bash
source venv/bin/activate
pip install -r requirements.txt
python seed.py
python run.py
```

Then open:

**Frontend**

http://127.0.0.1:5000/app

**Swagger**

http://127.0.0.1:5000/apidocs/

Run tests with:

```bash
pytest
```


