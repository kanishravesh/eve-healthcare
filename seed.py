from app import create_app, db
from app.models import Centre, Test

app = create_app()

with app.app_context():
    centre1 = Centre(
        name="EVE Diagnostics",
        location="Delhi"
    )

    centre2 = Centre(
        name="HealthCare Labs",
        location="Gurugram"
    )

    db.session.add_all([centre1, centre2])
    db.session.commit()

    tests = [
        Test(name="CBC", price=500, centre_id=centre1.id),
        Test(name="Blood Sugar", price=300, centre_id=centre1.id),
        Test(name="Thyroid Test", price=700, centre_id=centre2.id),
        Test(name="Lipid Profile", price=800, centre_id=centre2.id)
    ]

    db.session.add_all(tests)
    db.session.commit()

    print("Sample data added")