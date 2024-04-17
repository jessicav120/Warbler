"""Tests for user views"""
import os
from unittest import TestCase
from models import db, connect_db, Message, User, Likes, Follows

os.environ['DATABASE_URL'] =  'postgresql:///warbler-test'
from app import app, CURR_USER_KEY
db.create_all()

app.config['WTF_CSRF_ENABLED'] = False
class UserViewTestCase(TestCase):
    """Test views for users."""
    
    def setUp(self):
        """Create test client, add sample data"""
        
        User.query.delete()
        Message.query.delete()
        Likes.query.delete()
        Follows.query.delete()
        
        self.testuser = User(
            id=1,
            username='testuser',
            email='testuser@email.com',
            password='password',
            image_url=None
        )
        self.user2 = User(
            id=2,
            username='user2',
            email='user2@email.com',
            password='password',
            image_url=None
        )
        self.user3 = User(
            id=3,
            username='user3',
            email='user3@email.com',
            password='password',
            image_url=None
        )
        
        db.session.add_all([self.testuser, self.user2, self.user3])
        db.session.commit()
        
        self.client = app.test_client()
        
        
    def tearDown(self) -> None:
        """Teardown test case super class"""
        res = super().tearDown()
        db.session.rollback()
        return res
    
    # ------- set up follow function ----------
    def followSetUp(self):
        """Set up testuser to follow user3"""
        
        f = Follows(user_being_followed_id=self.user3.id, user_following_id=self.testuser.id)
        db.session.add(f)
        db.session.commit()
        
    #################################################################
    # SHOW USERS TESTS    
    #################################################################    
    def test_show_users_list(self):
        """Show general list of users"""
        with self.client as c: 
            resp = c.get('/users')
            res_str = str(resp.data)
            
            self.assertIn('@testuser', res_str)
            self.assertIn('@user2', res_str)
            self.assertIn('@user3', res_str)
        
    def test_show_user(self):
        """Does user details page show?"""
        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}")
            res_str = str(resp.data)
            
            self.assertIn('testuser', res_str)
            
    def test_show_following(self):
        """Is following list shown on profile when logged in?"""
        # set testuser following user3
        self.followSetUp()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id 
            
            resp = c.get(f"/users/{self.testuser.id}/following")
            res_str = str(resp.data)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", res_str)
            self.assertIn("user3", res_str)
            self.assertNotIn("user2", res_str)
            
    def test_show_followers(self):
        """Is followers list shown on profile when logged in?"""
        # set testuser following user3
        self.followSetUp()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            #show followers of user3
            resp = c.get(f"/users/{self.user3.id}/followers")
            res_str = str(resp.data)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", res_str)
            self.assertNotIn("user2", res_str)
    
    def test_nouser_show_following(self):
        """If not logged in, is access to following page denied?"""
        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/following", follow_redirects=True)
            res_str = str(resp.data)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", res_str)
            
    def test_nouser_show_followers(self):
        """If not logged in, is acces to follower page denied?"""
        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)
            res_str = str(resp.data)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", res_str)            
            
    #################################################################
    # FOLLOW USERS TESTS    
    ################################################################# 
    def test_add_follow(self):
        """Is user successfully followed if user is logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY]=self.testuser.id
            #have testuser follow user 2
            resp = c.post(f"/users/follow/{self.user2.id}", follow_redirects=True)
            res_str = str(resp.data)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("user2", res_str)
            self.assertIn('<h4 id="sidebar-username">@testuser</h4>', res_str) #show this is testuser's profile
            self.assertEqual(len(self.testuser.following), 1)
            
    def test_add_follow_nouser(self):
        """Does adding a follow fail if no user logged in?"""
        
        with self.client as c:    
            resp = c.post(f"/users/follow/{self.testuser.id}", follow_redirects=True)
            res_str = str(resp.data)
                
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", res_str)
            
    def test_delete_followers(self):
        """Is followers list shown on profile when logged in?"""
        # set testuser following user3
        self.followSetUp()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            #show followers of user3
            resp = c.post(f"/users/stop-following/{self.user3.id}", follow_redirects=True)
            res_str = str(resp.data)
            
            #testuser should not have user3 in the following page
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", res_str)
            self.assertNotIn("user3", res_str)
            self.assertEqual(len(self.testuser.following), 0)
            
    def test_delete_followers_unauthorized(self):
        """Does unfollowing fail if unauthorized user is attempting unfollow?"""
        self.followSetUp()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 2050 #non-existent user
                
            resp = c.post(f"/users/stop-following/{self.user3.id}", follow_redirects=True)
            res_str = str(resp.data)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", res_str)