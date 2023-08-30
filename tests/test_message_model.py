"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError, DataError
from flask import session, g

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()
app.config['WTF_CSRF_ENABLED'] = False

class MessageModelTestCase(TestCase):
    """Test model for messages."""

    def setUp(self):
        """Create test client, add sample data.
        Sign in to user profile."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()


    def tearDown(self):
        with app.app_context():
            db.session.remove()


    def test_messages_model(self):
        """Does basic model work?"""
        u = User.query.filter_by(username='testuser').first()

        new_message = Message(
            text = 'This is a warble.',
            timestamp = None,
            user_id = u.id
        )
        db.session.add(new_message)
        db.session.commit()

        # ensure message in db with default timestamp and correct signed in user
        message = Message.query.filter_by(text='This is a warble.').first()
        self.assertEqual(message.text, 'This is a warble.')
        self.assertIsNotNone(message.timestamp)
        self.assertEqual(message.user_id, u.id)
        self.assertEqual(message.user, u)

        # ensure redirection from messages if not logged in
        with app.test_client() as client:
            response = client.get('/messages/new')
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 302)

        # ensure viewing messages page when signed in and submitting get request
        CURR_USER_KEY = "curr_user"
        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = u.id
        
            g.user = User.query.get(session[CURR_USER_KEY])
            response = self.client.get('/messages/new', follow_redirects=True)
            html = response.get_data(as_text=True)
            
            # viewing 200 status code and message form
            self.assertEqual(response.status_code, 200)
            self.assertIn("Add my message!", html)

            # ensure post request results in redirect
            response = c.post('/messages/new', data={'text': 'hello'})
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 302)
        
            # ensure submitting new message works
            msg = Message.query.filter_by(text="hello").first()
            self.assertEqual(msg.text, "hello")







