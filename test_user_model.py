"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


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

        db.drop_all()
        db.create_all()
        
        #added
        user = User.signup(
            "usertest",
            "test@email.com",
            "HASHED",
            None
        )
        user2 = User.signup(
            "usertest2",
            "test2@email.com",
            "HASHED",
            None
        )
        db.session.add_all([user, user2])
        db.session.commit()
        
        u1 = user.id
        u2 = user2.id
        self.user = User.query.get(u1)
        self.user2 = User.query.get(u2)
        
        self.client = app.test_client()
        
    def tearDown(self):
        '''Rollback any failed transactions'''
        
        db.session.rollback()
        
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
    
    #################################################################
    # REPR METHOD TEST
   #################################################################
    def test_repr_method(self):
        """Does repr method work?"""
        
        repr_str = repr(self.user)
        
        #repr string should contain these:
        self.assertIn('User', repr_str)
        self.assertIn('test@email.com', repr_str)
        self.assertIn('usertest', repr_str)
    
    #################################################################
    # FOLLOWING TEST
    ##################################################################
    def test_is_following(self):
        """Detects if user is following user2"""
        #create Follows instance - user following user2
        f = Follows(user_being_followed_id=self.user2.id, user_following_id=self.user.id)
        db.session.add(f)
        db.session.commit()
        
        #user should now be following user2
        self.assertTrue(self.user.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user))
        
        self.assertEqual(len(self.user2.followers), 1)
        self.assertEqual(len(self.user.following), 1)
        self.assertEqual(len(self.user.followers), 0)
        self.assertEqual(len(self.user2.following), 0)
    
    #################################################################
    # FOLLOWER TEST 
    ##################################################################
    def test_is_followed(self):
        """Detect if user is being followed by user2"""

        #create Follows instance
        f = Follows(user_being_followed_id=self.user.id, user_following_id=self.user2.id)
        db.session.add(f)
        db.session.commit()
        
        #user should now be followed by user2
        self.assertTrue(self.user.is_followed_by(self.user2))
        self.assertFalse(self.user2.is_followed_by(self.user))
        
        self.assertEqual(len(self.user.followers), 1)
        self.assertEqual(len(self.user2.followers), 0)
        self.assertEqual(len(self.user2.following), 1)
    
    #################################################################
    # SIGNUP TESTS
    #################################################################
    
    def test_user_signup(self):
        """Does user signup work"""
        singup_test = User.signup('validuser', 'valid@email.com', 'password', None)
        usr_id = 800
        singup_test.id = usr_id
        db.session.commit()
        
        u = User.query.get(usr_id)
        self.assertIsNotNone(u)
        self.assertEqual(u.username, 'validuser')
        self.assertEqual(u.email, 'valid@email.com')
        
        self.assertIsInstance(u, User)
        #check password properly hashed
        self.assertTrue(u.password.startswith("$2b$"))
        
    def test_invalid_username(self):
        """Does signup fail with invalid username"""
        bad_username = User.signup(None, 'valid@email.com', 'password', None)
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()
            
    def test_invalid_password(self):
        """Does signup fail with invalid password"""
        #empty string password
        with self.assertRaises(ValueError):
            User.signup('validuser', 'valid@email.com', '', None)
        
        #None/null password
        with self.assertRaises(ValueError):
            User.signup('validuser', 'valid@email.com', None, None)
            
    def test_invalid_email(self):
        """Does signup fail with invalid email"""
        User.signup('validuser', None, 'password', None)
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()
            
    #################################################################
    # AUTHENTICATION TESTS
    #################################################################
    
    def test_authenticate_user(self):
        """Is a user returned if password is valid"""
        usr = User.authenticate('usertest', 'HASHED')
        
        self.assertIsNotNone(usr)
        self.assertIsInstance(usr, User)
        
    def test_auth_invalid_username(self):
        """Does authentication fail with invalid username or password?"""
        
        bad_usr = User.authenticate('badUser', 'HASHED')
        bad_pass = User.authenticate('usertest', 'badpassword')
        
        #invalid username
        self.assertFalse(bad_usr)
        #invalid password
        self.assertFalse(bad_pass)