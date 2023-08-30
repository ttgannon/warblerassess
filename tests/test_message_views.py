"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        db.session.commit()

        message = Message(
            text = 'This is a warble.',
            timestamp = None,
            user_id = self.testuser.id
        )
        db.session.add(message)
        db.session.commit()
        

    def test_messages(self):
        """Can user add and delete messages?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)
            
            # Available in database
            msg = Message.query.filter_by(text="Hello").first()
            self.assertEqual(msg.text, "Hello")

            # HTML redirects appropriately
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn("Hello", html)

            # deleting status code 302
            resp = c.post(f"/messages/{msg.id}/delete")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 302)
            
            # deleting html does not include msg.text and renders new template
            msg = Message.query.first()
            
            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(f"{msg.text}", html)  
    

    def test_delete_logged_out(self):
        # when logged out redirects
        msg = Message.query.first()
        resp = self.client.post(f'/messages/{msg.id}/delete')
        self.assertEqual(resp.status_code, 302)

        #when logged out unauthorized
        resp = self.client.post(f'/messages/{msg.id}/delete', follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertIn("unauthorized", html)
        
    def test_add_message_logged_out(self):
        """User logged out and adding messages"""
        # when logged out redirects
        resp = self.client.post('/messages/new', data={"text": "Hello"})
        self.assertEqual(resp.status_code, 302)

        #when logged out flashes unauthorized
        resp = self.client.post('/messages/new', data={"text": "Hello"}, follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertIn("unauthorized", html)


    def test_adding_improper_message(self):
        """Can user add and delete messages to other people's accounts?"""
        not_current_user = 999
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = not_current_user
            
            # Make sure adding new redirects
            resp = c.post("/messages/new", data={"text": "Hello"})
            self.assertEqual(resp.status_code, 302)

            # ensure adding new is unauthorized
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn("unauthorized", html)

            # ensure deleting redirects
            msg = Message.query.first()
            resp = c.post(f"/messages/{msg.id}/delete", data={"text": "Hello"})
            self.assertEqual(resp.status_code, 302)

            # ensure deleting is unauthorized
            resp = c.post(f"/messages/{msg.id}/delete", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn("unauthorized", html)
            

            

    