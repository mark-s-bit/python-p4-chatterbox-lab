import pytest
from datetime import datetime
from app import app, db, Message

@pytest.fixture
def client():
    """Create a test client and an in-memory database."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use an in-memory database
    with app.app_context():
        db.create_all()  # Create the database tables
        yield app.test_client()  # Provide the test client
        db.drop_all()  # Clean up after tests

@pytest.fixture
def init_database(client):
    """Create a test database with initial data."""
    with app.app_context():
        db.create_all()
        # Add a test message
        message = Message(body="Test message", username="Tester")
        db.session.add(message)
        db.session.commit()

def test_has_correct_columns(client):
    """Test Message model has correct columns."""
    with app.app_context():
        hello_from_liza = Message(body="Hello 👋", username="Liza")
        db.session.add(hello_from_liza)
        db.session.commit()

        assert hello_from_liza.body == "Hello 👋"
        assert hello_from_liza.username == "Liza"
        assert isinstance(hello_from_liza.created_at, datetime)

        db.session.delete(hello_from_liza)
        db.session.commit()

def test_returns_list_of_json_objects_for_all_messages_in_database(client, init_database):
    """Returns a list of JSON objects for all messages in the database."""
    with app.app_context():
        response = client.get('/messages')
        records = Message.query.all()

        for message in response.json:
            assert message['id'] in [record.id for record in records]
            assert message['body'] in [record.body for record in records]

def test_creates_new_message_in_the_database(client):
    """Creates a new message in the database."""
    with app.app_context():
        response = client.post('/messages', json={"body": "Hello 👋", "username": "Liza"})
        assert response.status_code == 201  # Check if creation was successful

        h = Message.query.filter_by(body="Hello 👋").first()
        assert h is not None  # Ensure the message is created

        db.session.delete(h)
        db.session.commit()

def test_returns_data_for_newly_created_message_as_json(client):
    """Returns data for the newly created message as JSON."""
    with app.app_context():
        response = client.post('/messages', json={"body": "Hello 👋", "username": "Liza"})
        assert response.content_type == 'application/json'

        assert response.json["body"] == "Hello 👋"
        assert response.json["username"] == "Liza"

        h = Message.query.filter_by(body="Hello 👋").first()
        assert h is not None

        db.session.delete(h)
        db.session.commit()

def test_updates_body_of_message_in_database(client, init_database):
    """Updates the body of a message in the database."""
    with app.app_context():
        m = Message.query.first()
        assert m is not None  # Ensure we have a message
        id = m.id

        response = client.patch(f'/messages/{id}', json={"body": "Goodbye 👋"})
        assert response.status_code == 200

        g = Message.query.get(id)
        assert g.body == "Goodbye 👋"  # Verify the update

        # Reset the body back to original
        g.body = m.body
        db.session.commit()

def test_returns_data_for_updated_message_as_json(client, init_database):
    """Returns data for the updated message as JSON."""
    with app.app_context():
        m = Message.query.first()
        assert m is not None  # Ensure we have a message
        id = m.id

        response = client.patch(f'/messages/{id}', json={"body": "Goodbye 👋"})
        assert response.content_type == 'application/json'
        assert response.json["body"] == "Goodbye 👋"

        # Reset the body back to original
        g = Message.query.get(id)
        g.body = m.body
        db.session.commit()

def test_deletes_message_from_database(client):
    """Deletes the message from the database."""
    with app.app_context():
        hello_from_liza = Message(body="Hello 👋", username="Liza")
        db.session.add(hello_from_liza)
        db.session.commit()

        response = client.delete(f'/messages/{hello_from_liza.id}')
        assert response.status_code == 204  # Check if deletion was successful

        h = Message.query.filter_by(body="Hello 👋").first()
        assert h is None  # Ensure the message was deleted

# Run tests if this file is executed directly
if __name__ == "__main__":
    pytest.main()
