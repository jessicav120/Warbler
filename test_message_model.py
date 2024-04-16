"""Messsage model tests"""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test Message Model"""
    
    def setUp(self):
        """Create test client & add sample data."""
        
        db.drop_all()
        db.create_all()
        
        usr = User.signup("testuser", "test@email.com", "password", None)
        db.session.commit()
       
        self.user = usr

        self.client = app.test_client()
        
    def tearDown(self):
        """Rollback any failed transactions"""
        
        db.session.rollback()
        
    def test_message_model(self):
        """Does basic model work?"""
        
        msg = Message(
            text='testing text',
            user_id=self.user.id
        )
        db.session.add(msg)
        db.session.commit()
        
        self.assertEqual('testing text', msg.text)
        self.assertIsInstance(msg, Message)
        
    def test_msg_user_relationship(self):
        """Is the relationship btwn msg and user successfully established?"""
        uid = self.user.id
        user_messages = self.user.messages

        msg = Message(text="New Msg Txt")
        user_messages.append(msg)
        db.session.commit()
        
        #self.user should have a message. 
        self.assertEqual(len(user_messages), 1)
        self.assertEqual(msg.user_id, uid)
        self.assertIn(msg, user_messages)
        
    def test_ivalid_user(self):
        """Does message creation fail with missing user?"""
        bad_msg= Message(text='bad test text')
        db.session.add(bad_msg)
        
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()
            
    def test_ivalid_text(self):
        """Does message creation fail with missing text?"""
        bad_msg= Message(text=None, user_id=self.user.id)
        db.session.add(bad_msg)
        
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()
            
    def test_timestamp(self):
        """Is timestamp successfully created?"""
        msg = Message(text='text', user_id=self.user.id)
        db.session.add(msg)
        db.session.commit()
        
        self.assertIsNotNone(msg.timestamp)