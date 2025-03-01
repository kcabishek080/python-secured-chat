import unittest
import os
import sqlite3
import tempfile
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QPushButton, QLineEdit

from login_gui import LoginSignupGUI
from db import create_table, register_user

# Create QApplication instance for tests
app = QApplication(sys.argv)

class TestLoginIntegration(unittest.TestCase):
    """Integration tests for the login system and database."""
    
    def setUp(self):
        """Set up test environment."""
        # Use a temporary file for the test database
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Override sqlite3.connect to use our test database
        self._original_connect = sqlite3.connect
        def mock_connect(database_name, *args, **kwargs):
            if database_name == 'users.db':
                return self._original_connect(self.db_path, *args, **kwargs)
            return self._original_connect(database_name, *args, **kwargs)
        sqlite3.connect = mock_connect
        
        # Create the test database and table
        create_table()
        
        # Create a test user
        register_user('testuser', 'testpass')
        
        # Create the login GUI
        self.login_gui = LoginSignupGUI()
    
    def tearDown(self):
        """Clean up after tests."""
        self.login_gui.close()
        sqlite3.connect = self._original_connect
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_successful_login(self):
        """Test successful login with valid credentials."""
        # Set up signal tracking
        self.login_success_received = False
        self.login_username_received = None
        
        def on_login_successful(username):
            self.login_success_received = True
            self.login_username_received = username
        
        self.login_gui.login_successful.connect(on_login_successful)
        
        # Enter login credentials
        username_field = self.login_gui.login_username
        password_field = self.login_gui.login_password
        
        username_field.setText('testuser')
        password_field.setText('testpass')
        
        # Find and click the login button
        login_button = None
        for child in self.login_gui.findChildren(QPushButton):
            if child.text() == "Login":
                login_button = child
                break
        
        self.assertIsNotNone(login_button)
        QTest.mouseClick(login_button, Qt.LeftButton)
        
        # Check that login was successful
        self.assertTrue(self.login_success_received)
        self.assertEqual(self.login_username_received, 'testuser')
    
    def test_failed_login(self):
        """Test failed login with invalid credentials."""
        # Set up signal tracking
        self.login_success_received = False
        
        def on_login_successful(username):
            self.login_success_received = True
        
        self.login_gui.login_successful.connect(on_login_successful)
        
        # Enter invalid login credentials
        username_field = self.login_gui.login_username
        password_field = self.login_gui.login_password
        
        username_field.setText('testuser')
        password_field.setText('wrongpass')
        
        # Find and click the login button
        login_button = None
        for child in self.login_gui.findChildren(QPushButton):
            if child.text() == "Login":
                login_button = child
                break
        
        self.assertIsNotNone(login_button)
        
        # Use a timer to close the error message box
        def close_message_box():
            # Find active QMessageBox and close it
            for widget in QApplication.topLevelWidgets():
                if widget.isVisible() and widget.metaObject().className() == 'QMessageBox':
                    QTest.keyClick(widget, Qt.Key_Enter)
        
        QTimer.singleShot(100, close_message_box)
        
        # Click login button
        QTest.mouseClick(login_button, Qt.LeftButton)
        
        # Process events to ensure signal handling completes
        QApplication.processEvents()
        
        # Check that login failed
        self.assertFalse(self.login_success_received)
    
    def test_successful_signup_then_login(self):
        """Test successful signup followed by login."""
        # Go to signup page
        self.login_gui.stacked_widget.setCurrentIndex(1)
        
        # Fill in signup form
        self.login_gui.signup_username.setText('newuser')
        self.login_gui.signup_password.setText('newpass')
        self.login_gui.signup_confirm.setText('newpass')
        
        # Find signup button
        signup_button = None
        for child in self.login_gui.signup_page.findChildren(QPushButton):
            if child.text() == "Create Account":
                signup_button = child
                break
        
        self.assertIsNotNone(signup_button)
        
        # Use a timer to close the success message box
        def close_message_box():
            for widget in QApplication.topLevelWidgets():
                if widget.isVisible() and widget.metaObject().className() == 'QMessageBox':
                    QTest.keyClick(widget, Qt.Key_Enter)
        
        QTimer.singleShot(100, close_message_box)
        
        # Click signup button
        QTest.mouseClick(signup_button, Qt.LeftButton)
        
        # Process events to ensure signal handling completes
        QApplication.processEvents()
        
        # The login page should now be showing with username prefilled
        self.assertEqual(self.login_gui.stacked_widget.currentIndex(), 0)
        self.assertEqual(self.login_gui.login_username.text(), 'newuser')
        
        # Set up login success signal tracking
        self.login_success_received = False
        self.login_username_received = None
        
        def on_login_successful(username):
            self.login_success_received = True
            self.login_username_received = username
        
        self.login_gui.login_successful.connect(on_login_successful)
        
        # Enter password
        self.login_gui.login_password.setText('newpass')
        
        # Find login button
        login_button = None
        for child in self.login_gui.login_page.findChildren(QPushButton):
            if child.text() == "Login":
                login_button = child
                break
        
        self.assertIsNotNone(login_button)