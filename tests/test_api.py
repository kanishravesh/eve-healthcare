import pytest

from app import create_app, db
from app.models import Payment


@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def create_user_and_login(client):
    client.post(
        "/signup",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }
    )

    response = client.post(
        "/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    return response.json["access_token"]


def create_booking(client, token):
    response = client.post(
        "/bookings",
        json={
            "test_id": 1,
            "centre_id": 1,
            "appointment_time": "2026-10-01T10:00:00"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    return response.json["booking_id"]


def test_signup(client):
    response = client.post(
        "/signup",
        json={
            "name": "Kanish",
            "email": "kanish@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 201


def test_login(client):
    client.post(
        "/signup",
        json={
            "name": "Kanish",
            "email": "kanish@example.com",
            "password": "password123"
        }
    )

    response = client.post(
        "/login",
        json={
            "email": "kanish@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json


def test_me(client):
    token = create_user_and_login(client)

    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json["email"] == "test@example.com"


def test_create_booking(client):
    token = create_user_and_login(client)

    # Create test data for this isolated test database
    from app.models import Centre, Test

    with client.application.app_context():
        centre = Centre(
            name="Test Centre",
            location="Delhi"
        )
        db.session.add(centre)
        db.session.commit()

        test = Test(
            name="CBC",
            price=500,
            centre_id=centre.id
        )
        db.session.add(test)
        db.session.commit()

        test_id = test.id
        centre_id = centre.id

    response = client.post(
        "/bookings",
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_time": "2026-10-01T10:00:00"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    assert response.json["status"] == "PENDING"


def test_payment_success(client):
    token = create_user_and_login(client)

    from app.models import Centre, Test

    with client.application.app_context():
        centre = Centre(
            name="Test Centre",
            location="Delhi"
        )
        db.session.add(centre)
        db.session.commit()

        test = Test(
            name="CBC",
            price=500,
            centre_id=centre.id
        )
        db.session.add(test)
        db.session.commit()

        test_id = test.id
        centre_id = centre.id

    booking_id = create_booking(client, token)

    response = client.post(
        "/payments",
        json={
            "booking_id": booking_id,
            "status": "SUCCESS"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    assert response.json["booking_status"] == "CONFIRMED"


def test_payment_failed(client):
    token = create_user_and_login(client)

    from app.models import Centre, Test

    with client.application.app_context():
        centre = Centre(
            name="Test Centre",
            location="Delhi"
        )
        db.session.add(centre)
        db.session.commit()

        test = Test(
            name="CBC",
            price=500,
            centre_id=centre.id
        )
        db.session.add(test)
        db.session.commit()

    booking_id = create_booking(client, token)

    response = client.post(
        "/payments",
        json={
            "booking_id": booking_id,
            "status": "FAILED"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    assert response.json["booking_status"] == "FAILED"


def test_duplicate_webhook(client):
    token = create_user_and_login(client)

    from app.models import Centre, Test

    with client.application.app_context():
        centre = Centre(
            name="Test Centre",
            location="Delhi"
        )
        db.session.add(centre)
        db.session.commit()

        test = Test(
            name="CBC",
            price=500,
            centre_id=centre.id
        )
        db.session.add(test)
        db.session.commit()

    booking_id = create_booking(client, token)

    webhook_data = {
        "event_id": "event-123",
        "booking_id": booking_id,
        "status": "SUCCESS"
    }

    first = client.post(
        "/payments/webhook",
        json=webhook_data
    )

    second = client.post(
        "/payments/webhook",
        json=webhook_data
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json["message"] == "Event already processed"

    with client.application.app_context():
        assert Payment.query.count() == 1


def test_user_cannot_pay_another_users_booking(client):
    token1 = create_user_and_login(client)

    from app.models import Centre, Test

    with client.application.app_context():
        centre = Centre(
            name="Test Centre",
            location="Delhi"
        )
        db.session.add(centre)
        db.session.commit()

        test = Test(
            name="CBC",
            price=500,
            centre_id=centre.id
        )
        db.session.add(test)
        db.session.commit()

    booking_id = create_booking(client, token1)

    # Create second user
    client.post(
        "/signup",
        json={
            "name": "Second User",
            "email": "second@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/login",
        json={
            "email": "second@example.com",
            "password": "password123"
        }
    )

    token2 = login_response.json["access_token"]

    response = client.post(
        "/payments",
        json={
            "booking_id": booking_id,
            "status": "SUCCESS"
        },
        headers={"Authorization": f"Bearer {token2}"}
    )

    assert response.status_code == 404