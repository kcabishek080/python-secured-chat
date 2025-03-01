import unittest
import os
import sqlite3
from db import create_table, register_user, validate_login, hash_password

class TestDatabase(unittest.TestCase):
    """Test cases for the database operations."""
    
    def setUp(self):
        """Set up test environment - use a test database file."""
        # Use a test database file
        self.db_name = 'test_users.db'
        
        # Ensure we're using the test database
        self._original_connect = sqlite3.connect
        def mock_connect(database_name, *args, **kwargs):
            if database_name == 'users.db':
                return self._original_connect(self.db_name, *args, **kwargs)
            return self._original_connect(database_name, *args, **kwargs)
        sqlite3.connect = mock_connect
        
        # Create the test database and table
        create_table()
    
    def tearDown(self):
        """Clean up after tests - remove the test database."""
        sqlite3.connect = self._original_connect
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
    
    def test_create_table(self):
        """Test that the users table is created correctly."""
        # The table should already be created by setUp
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Check if the users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table = cursor.fetchone()
        self.assertIsNotNone(table)
        
        # Check the table structure
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        # Expected columns: id, username, password
        self.assertEqual(len(columns), 3)
        
        column_names = [col[1] for col in columns]
        self.assertIn('id', column_names)
        self.assertIn('username', column_names)
        self.assertIn('password', column_names)
        
        conn.close()
    
    def test_register_user_success(self):
        """Test successful user registration."""
        result = register_user('testuser', 'testpassword')
        self.assertTrue(result)
        
        # Verify the user was added to the database
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username=?", ('testuser',))
        user = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(user)
        self.assertEqual(user[0], 'testuser')
    
    def test_register_user_duplicate(self):
        """Test that registering a duplicate username fails."""
        # Register a user
        register_user('testuser', 'testpassword')
        
        # Try to register the same username again
        result = register_user('testuser', 'different_password')
        self.assertFalse(result)
    
    def test_validate_login_success(self):
        """Test successful login validation."""
        # Register a user
        register_user('loginuser', 'loginpassword')
        
        # Test valid credentials
        result = validate_login('loginuser', 'loginpassword')
        self.assertTrue(result)
    
    def test_validate_login_wrong_password(self):
        """Test login validation with wrong password."""
        # Register a user
        register_user('loginuser', 'loginpassword')
        
        # Test invalid password
        result = validate_login('loginuser', 'wrongpassword')
        self.assertFalse(result)
    
    def test_validate_login_nonexistent_user(self):
        """Test login validation with a nonexistent user."""
        result = validate_login('nonexistentuser', 'anypassword')
        self.assertFalse(result)
    
    def test_password_hashing(self):
        """Test that password hashing works correctly."""
        password = "mySecurePassword123"
        hashed = hash_password(password)
        
        # Hash should be a string
        self.assertIsInstance(hashed, str)
        
        # Hash should not be the plain password
        self.assertNotEqual(hashed, password)
        
        # Same password should produce the same hash
        self.assertEqual(hashed, hash_password(password))
        
        # Different passwords should produce different hashes
        self.assertNotEqual(hashed, hash_password("differentPassword"))


if __name__ == '__main__':
    unittest.main()