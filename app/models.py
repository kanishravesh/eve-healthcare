from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Centre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)


class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    centre_id = db.Column(db.Integer, db.ForeignKey("centre.id"), nullable=False)
    
    
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey("test.id"), nullable=False)
    centre_id = db.Column(db.Integer, db.ForeignKey("centre.id"), nullable=False)

    appointment_time = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="PENDING", nullable=False)    
    
    
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("booking.id"),
        nullable=False
    )

    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)    
    
    
class WebhookEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(100), unique=True, nullable=False)        