from flask import Blueprint, request, render_template
from app import db
from app.models import User, Centre, Test, Booking, Payment, WebhookEvent
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import bcrypt
from datetime import datetime
import logging


routes = Blueprint("routes", __name__)

logger = logging.getLogger(__name__)


@routes.route("/")
def home():
    return {"message": "EVE Healthcare API is running"}


@routes.route("/signup", methods=["POST"])
def signup():
    """
    Register a new user.

    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - password
          properties:
            name:
              type: string
            email:
              type: string
            password:
              type: string
    responses:
      201:
        description: User registered successfully
      400:
        description: Invalid request
      409:
        description: Email already registered
    """
    data = request.get_json()

    if not data or not data.get("name") or not data.get("email") or not data.get("password"):
        return {"error": "Name, email and password are required"}, 400

    existing_user = User.query.filter_by(email=data["email"]).first()

    if existing_user:
        return {"error": "Email already registered"}, 409

    password = bcrypt.hashpw(
        data["password"].encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    user = User(
        name=data["name"],
        email=data["email"],
        password=password
    )

    db.session.add(user)
    db.session.commit()

    logger.info("user_registered user_id=%s", user.id)

    return {
        "message": "User registered successfully",
        "user_id": user.id
    }, 201


@routes.route("/login", methods=["POST"])
def login():
    """
    Login and receive a JWT access token.

    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful
      400:
        description: Missing credentials
      401:
        description: Invalid credentials
    """
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return {"error": "Email and password are required"}, 400

    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return {"error": "Invalid email or password"}, 401

    password_ok = bcrypt.checkpw(
        data["password"].encode("utf-8"),
        user.password.encode("utf-8")
    )

    if not password_ok:
        return {"error": "Invalid email or password"}, 401

    token = create_access_token(identity=str(user.id))

    logger.info("user_login user_id=%s", user.id)

    return {
        "message": "Login successful",
        "access_token": token
    }


@routes.route("/me")
@jwt_required()
def me():
    """
    Get the currently logged-in user.

    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Current user details
      401:
        description: Missing or invalid token
      404:
        description: User not found
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user:
        return {"error": "User not found"}, 404

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email
    }


@routes.route("/centres", methods=["GET"])
def get_centres():
    """
    Get all diagnostic centres.

    ---
    tags:
      - Centres and Tests
    responses:
      200:
        description: List of diagnostic centres
    """
    centres = Centre.query.all()

    return [
        {
            "id": centre.id,
            "name": centre.name,
            "location": centre.location
        }
        for centre in centres
    ]


@routes.route("/centres/<int:centre_id>/tests", methods=["GET"])
def get_tests(centre_id):
    """
    Get tests available at a diagnostic centre.

    ---
    tags:
      - Centres and Tests
    parameters:
      - name: centre_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: List of tests
      404:
        description: Centre not found
    """
    centre = db.session.get(Centre, centre_id)

    if not centre:
        return {"error": "Centre not found"}, 404

    tests = Test.query.filter_by(centre_id=centre_id).all()

    return [
        {
            "id": test.id,
            "name": test.name,
            "price": test.price
        }
        for test in tests
    ]


@routes.route("/bookings", methods=["POST"])
@jwt_required()
def create_booking():
    """
    Create a diagnostic test booking.

    ---
    tags:
      - Bookings
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - test_id
            - centre_id
            - appointment_time
          properties:
            test_id:
              type: integer
            centre_id:
              type: integer
            appointment_time:
              type: string
              example: "2026-10-01T10:30:00"
    responses:
      201:
        description: Booking created
      400:
        description: Invalid request
      401:
        description: Missing or invalid token
      404:
        description: Test or centre not found
    """
    data = request.get_json()

    if not data:
        return {"error": "Request body is required"}, 400

    test = db.session.get(Test, data.get("test_id"))
    centre = db.session.get(Centre, data.get("centre_id"))

    if not test or not centre:
        return {"error": "Test or centre not found"}, 404

    if test.centre_id != centre.id:
        return {"error": "Test is not available at this centre"}, 400

    if not data.get("appointment_time"):
        return {"error": "Appointment time is required"}, 400

    try:
        appointment_time = datetime.fromisoformat(
            data["appointment_time"]
        )
    except ValueError:
        return {"error": "Invalid appointment time"}, 400

    user_id = int(get_jwt_identity())

    booking = Booking(
        user_id=user_id,
        test_id=test.id,
        centre_id=centre.id,
        appointment_time=appointment_time,
        amount=test.price
    )

    db.session.add(booking)
    db.session.commit()

    logger.info(
        "booking_created booking_id=%s user_id=%s amount=%s",
        booking.id,
        user_id,
        booking.amount
    )

    return {
        "message": "Booking created",
        "booking_id": booking.id,
        "status": booking.status,
        "amount": booking.amount
    }, 201


@routes.route("/payments", methods=["POST"])
@jwt_required()
def make_payment():
    """
    Process a simulated payment for a booking.

    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - booking_id
            - status
          properties:
            booking_id:
              type: integer
            status:
              type: string
              enum:
                - SUCCESS
                - FAILED
    responses:
      201:
        description: Payment processed
      400:
        description: Invalid payment request
      401:
        description: Missing or invalid token
      404:
        description: Booking not found
    """
    data = request.get_json()

    if not data:
        return {"error": "Request body is required"}, 400

    user_id = int(get_jwt_identity())

    # Only allow the owner of the booking to make its payment.
    booking = Booking.query.filter_by(
        id=data.get("booking_id"),
        user_id=user_id
    ).first()

    if not booking:
        return {"error": "Booking not found"}, 404

    if booking.status != "PENDING":
        return {"error": "Booking is not pending"}, 400

    payment_status = data.get("status")

    if payment_status not in ["SUCCESS", "FAILED"]:
        return {"error": "Invalid payment status"}, 400

    payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=payment_status
    )

    booking.status = (
        "CONFIRMED"
        if payment_status == "SUCCESS"
        else "FAILED"
    )

    db.session.add(payment)
    db.session.commit()

    logger.info(
        "payment_processed booking_id=%s user_id=%s status=%s",
        booking.id,
        user_id,
        payment_status
    )

    return {
        "message": "Payment processed",
        "payment_id": payment.id,
        "payment_status": payment.status,
        "booking_status": booking.status
    }, 201


@routes.route("/payments/webhook", methods=["POST"])
def payment_webhook():
    """
    Process a payment provider webhook.

    ---
    tags:
      - Payments
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - event_id
            - booking_id
            - status
          properties:
            event_id:
              type: string
            booking_id:
              type: integer
            status:
              type: string
              enum:
                - SUCCESS
                - FAILED
    responses:
      200:
        description: Webhook processed or already processed
      400:
        description: Invalid webhook data
      404:
        description: Booking not found
    """
    data = request.get_json()

    if not data:
        return {"error": "Request body is required"}, 400

    event_id = data.get("event_id")
    booking_id = data.get("booking_id")
    status = data.get("status")

    if not event_id or not booking_id or not status:
        return {"error": "Invalid webhook data"}, 400

    existing_event = WebhookEvent.query.filter_by(
        event_id=event_id
    ).first()

    if existing_event:
        logger.info(
            "duplicate_webhook event_id=%s",
            event_id
        )
        return {"message": "Event already processed"}, 200

    booking = db.session.get(Booking, booking_id)

    if not booking:
        return {"error": "Booking not found"}, 404

    if status not in ["SUCCESS", "FAILED"]:
        return {"error": "Invalid payment status"}, 400

    payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=status
    )

    booking.status = (
        "CONFIRMED"
        if status == "SUCCESS"
        else "FAILED"
    )

    event = WebhookEvent(event_id=event_id)

    db.session.add(payment)
    db.session.add(event)
    db.session.commit()

    logger.info(
        "webhook_processed event_id=%s booking_id=%s status=%s",
        event_id,
        booking.id,
        status
    )

    return {"message": "Webhook processed"}, 200


@routes.route("/bookings", methods=["GET"])
@jwt_required()
def get_bookings():
    """
    Get all bookings belonging to the logged-in user.

    ---
    tags:
      - Bookings
    security:
      - Bearer: []
    responses:
      200:
        description: List of user bookings
      401:
        description: Missing or invalid token
    """
    user_id = int(get_jwt_identity())

    bookings = Booking.query.filter_by(user_id=user_id).all()

    return [
        {
            "id": booking.id,
            "test_id": booking.test_id,
            "centre_id": booking.centre_id,
            "appointment_time": booking.appointment_time,
            "amount": booking.amount,
            "status": booking.status
        }
        for booking in bookings
    ]


@routes.route("/bookings/<int:booking_id>", methods=["GET"])
@jwt_required()
def get_booking(booking_id):
    """
    Get a specific booking.

    ---
    tags:
      - Bookings
    security:
      - Bearer: []
    parameters:
      - name: booking_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Booking details
      401:
        description: Missing or invalid token
      404:
        description: Booking not found
    """
    user_id = int(get_jwt_identity())

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=user_id
    ).first()

    if not booking:
        return {"error": "Booking not found"}, 404

    return {
        "id": booking.id,
        "test_id": booking.test_id,
        "centre_id": booking.centre_id,
        "appointment_time": booking.appointment_time,
        "amount": booking.amount,
        "status": booking.status
    }


@routes.route("/bookings/<int:booking_id>", methods=["DELETE"])
@jwt_required()
def cancel_booking(booking_id):
    """
    Cancel a pending booking.

    ---
    tags:
      - Bookings
    security:
      - Bearer: []
    parameters:
      - name: booking_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Booking cancelled
      400:
        description: Booking cannot be cancelled
      401:
        description: Missing or invalid token
      404:
        description: Booking not found
    """
    user_id = int(get_jwt_identity())

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=user_id
    ).first()

    if not booking:
        return {"error": "Booking not found"}, 404

    if booking.status != "PENDING":
        return {"error": "Only pending bookings can be cancelled"}, 400

    booking.status = "CANCELLED"
    db.session.commit()

    logger.info(
        "booking_cancelled booking_id=%s user_id=%s",
        booking.id,
        user_id
    )

    return {"message": "Booking cancelled"}


@routes.route("/app")
def frontend():
    return render_template("index.html")