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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()


    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

        # signup class method should work 
        user1 = User.signup(
            username="testuser10",
            email="hello123@gmail.com",
            password="HASHED_PWD",
            image_url="my_url"
        )
        db.session.commit()
        user1 = User.query.filter_by(username="testuser10").first()
        self.assertEqual(user1.email, "hello123@gmail.com")

        # user should be findable in the database, with username, email and default image values
        user = User.query.filter_by(username="testuser").first()
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@test.com")
        self.assertEqual(user.image_url, "/static/images/default-pic.png")
        self.assertEqual(user.header_image_url, "/static/images/warbler-hero.jpg")

        # testing repr method
        self.assertEqual(f'{user}', f'<User #{user.id}: testuser, test@test.com>')

        # should not be able to create duplicate email with different username
        u = User(
            email="test@test.com",
            username="newtestuser",
            password="HASHED_PASSWORD"
        )
        try:
            db.session.add(u)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            self.assertIn("duplicate key value violates unique constraint", str(e))
        
        # should not be able to create duplicate username with different email
        u = User(
            email="newtest@newtest.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        try:
            db.session.add(u)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            self.assertIn("duplicate key value violates unique constraint", str(e))
        
        # should not be able to create account with null username
        u = User.signup(
            email="whatever@unique_email.com",
            username=None,
            password="HASHED_PASSWORD",
            image_url='image'
        )
        try:
            db.session.commit()
        except (IntegrityError, DataError) as e:
            db.session.rollback()
            self.assertIn("violates not-null constraint", str(e))

        # should not be able to create account with null email
        u = User.signup(
            email=None,
            username="unique_username",
            password="HASHED_PASSWORD",
            image_url='image'
        )
        try:
            db.session.commit()
        except (IntegrityError, DataError) as e:
            db.session.rollback()
            self.assertIn("violates not-null constraint", str(e))
        
        # testing authenticate method -- proper email/password
        authentication = user.authenticate("testuser10", "HASHED_PWD")
        self.assertEqual(f'{authentication}', f'<User #{user1.id}: {user1.username}, {user1.email}>')

        # testing authenticate method -- improper email/password
        authentication = user.authenticate("testuser10", "false_password")
        self.assertFalse(authentication)
        
    def test_user_relationships(self):
        """Do relationships work?"""
        u1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add_all([u1,u2])
        db.session.commit()

        # ensure is_following and _is_followed_by FAIL when users are not following each other
        u1_follows_u2 = u2.is_followed_by(u1)
        u2_follows_u1 = u1.is_followed_by(u2)
        u1_follows_u2 = u1.is_following(u2)
        u2_follows_u1 = u2.is_following(u1)

        self.assertFalse(u1_follows_u2)
        self.assertFalse(u2_follows_u1)
        self.assertFalse(u1_follows_u2)
        self.assertFalse(u2_follows_u1)

        # ensure is_following and is_followed_by PASS when users are following each other
        CURR_USER_KEY = "curr_user"
        u1 = User.query.filter_by(username=u1.username).first()
        u2 = User.query.filter_by(username=u2.username).first()

        # sign in as u1
        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = u1.id
        
        #follow u2
        response = self.client.post(f'/users/follow/{u2.id}', follow_redirects=True)
        
        #test if u1 is following u2 using followers and following methods
        self.assertEqual(response.status_code, 200)
        self.assertTrue(u1 in u2.followers)
        self.assertTrue(u2 in u1.following)

        # html = response.get_data(as_text=True)

        