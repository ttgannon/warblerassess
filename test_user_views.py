"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes

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


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        

        not_current_user = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser",
                                    image_url=None)
        
        db.session.commit()

        message = Message(
            text = 'This is a warble.',
            timestamp = None,
            user_id = not_current_user.id
        )
        db.session.add(message)
        db.session.commit()
        

    def test_likes(self):
        "Can a user like another user's tweet?"
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # ensure user can like another's post
            message = Message.query.filter_by(text='This is a warble.').first()
            resp = c.post(f"/users/add_like/{message.id}")
            like = Likes.query.filter_by(message_id=message.id).first()
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(like.user_id, self.testuser.id)
            self.assertEqual(len(self.testuser.likes), 1)

            # ensure user can unlike another's post and is removed form the db
            message = Message.query.filter_by(text='This is a warble.').first()
            resp = c.post(f"/users/add_like/{message.id}")
            likes = Likes.query.filter_by(message_id=message.id).first()
            self.assertEqual(resp.status_code, 302)
            self.assertIsNone(likes)
            self.assertEqual(len(self.testuser.likes), 0)





    # def test_delete()
        
    # def test_stop_follow()
        
    # def test_follow()
        
    # def test_users()
            

            

    