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

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


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
        
    def tearDown(self): #added 
        """Clear any failed transactions"""
        
        db.session.rollback()
        
    #################################################################
    # MESSAGE CREATION TESTS    
    #################################################################
    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
            
    def test_add_msg_nouser(self):
        """Does adding new message fail if no user in session?"""
        
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            res_str = str(resp.data)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", res_str)
    
    def test_unauthorized_add_msg(self):
        """Does creating message fail if unauthorized user is trying to create?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY]= 2050 #non-existent user  
            resp = c.post("/messages/new", follow_redirects=True)
            res_str = str(resp.data)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", res_str)
    
    # ------ function for making a new message -------------
    def make_msg(self, custom_id):
        """make a sample message"""
        msg = Message(
            id=custom_id,
            text='test message',
            user_id=self.testuser.id
        )
        db.session.add(msg)
        db.session.commit()
        
        return msg
    
    #################################################################
    # SHOW MESSAGE TEST
    #################################################################
    def show_message(self):
        """Does the message show properly?"""
        msg = self.make_msg(100)
        
        with self.client as c:
            msg = Message.query.get(msg.id)
            
            resp = c.get(f"/messages/{msg.id}", follow_redirects=True)
            res_str = str(resp.data)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(msg.text, res_str)
        
    #################################################################
    # MESSAGE DELETION TESTS    
    #################################################################
            
    def test_delete_message(self):
        """Does delete message work?"""
        
        msg = self.make_msg(150)
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY]=self.testuser.id
            
            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            
            msg = Message.query.get(150)
            #msg should no longer exist
            self.assertIsNone(msg)
            self.assertEqual(len(self.testuser.messages), 0)
            
    def test_delete_msg_nouser(self):
        """Does message fail to delete when no user in session?"""
        
        msg = self.make_msg(50)
        
        with self.client as c:
            resp = c.post("/messages/50/delete", follow_redirects=True)
            res_str = str(resp.data) #get response data as a string
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", res_str)
            
            #msg should still exist
            msg = Message.query.get(50)
            self.assertIsNotNone(msg)
            
    def test_unathorized_delete_msg(self):
        """Dose deleting fail if incorrect user is attempting deletion?"""
        #message owned by test user
        msg = self.make_msg(300)
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 2050 #non-existent user
                
            resp = c.post("/messages/300/delete", follow_redirects=True)
            res_str = str(resp.data)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", res_str)
            
            msg = Message.query.get(300)
            self.assertIsNotNone(msg)
            
            