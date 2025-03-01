from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QStackedWidget, 
                             QMessageBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class LoginSignupGUI(QWidget):
    login_successful = pyqtSignal(str)  # Signal to emit when login is successful
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # Set window properties
        self.setWindowTitle('Secure Chat - Login')
        self.setMinimumSize(400, 300)
        
        # Create stacked widget to switch between login and signup
        self.stacked_widget = QStackedWidget()
        
        # Create login and signup pages
        self.login_page = self.create_login_page()
        self.signup_page = self.create_signup_page()
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.signup_page)
        
        # Set initial page to login
        self.stacked_widget.setCurrentIndex(0)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        
        self.setLayout(main_layout)
        
    def create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Welcome to Secure Chat")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        
        # Username
        username_label = QLabel("Username:")
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter your username")
        
        # Password
        password_label = QLabel("Password:")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Enter your password")
        self.login_password.setEchoMode(QLineEdit.Password)
        
        # Login button
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.handle_login)
        
        # Link to signup
        signup_text = QLabel("Don't have an account?")
        signup_link = QPushButton("Create account")
        signup_link.setFlat(True)
        signup_link.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        # Signup link layout
        signup_layout = QHBoxLayout()
        signup_layout.addWidget(signup_text)
        signup_layout.addWidget(signup_link)
        signup_layout.addStretch()
        
        # Add all widgets to layout
        layout.addWidget(title_label)
        layout.addSpacing(20)
        layout.addWidget(username_label)
        layout.addWidget(self.login_username)
        layout.addWidget(password_label)
        layout.addWidget(self.login_password)
        layout.addSpacing(10)
        layout.addWidget(login_button)
        layout.addSpacing(20)
        layout.addLayout(signup_layout)
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def create_signup_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Create an Account")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        
        # Username
        username_label = QLabel("Username:")
        self.signup_username = QLineEdit()
        self.signup_username.setPlaceholderText("Choose a username")
        
        # Password
        password_label = QLabel("Password:")
        self.signup_password = QLineEdit()
        self.signup_password.setPlaceholderText("Choose a password")
        self.signup_password.setEchoMode(QLineEdit.Password)
        
        # Confirm Password
        confirm_label = QLabel("Confirm Password:")
        self.signup_confirm = QLineEdit()
        self.signup_confirm.setPlaceholderText("Confirm your password")
        self.signup_confirm.setEchoMode(QLineEdit.Password)
        
        # Signup button
        signup_button = QPushButton("Create Account")
        signup_button.clicked.connect(self.handle_signup)
        
        # Link to login
        login_text = QLabel("Already have an account?")
        login_link = QPushButton("Login")
        login_link.setFlat(True)
        login_link.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        # Login link layout
        login_layout = QHBoxLayout()
        login_layout.addWidget(login_text)
        login_layout.addWidget(login_link)
        login_layout.addStretch()
        
        # Add all widgets to layout
        layout.addWidget(title_label)
        layout.addSpacing(20)
        layout.addWidget(username_label)
        layout.addWidget(self.signup_username)
        layout.addWidget(password_label)
        layout.addWidget(self.signup_password)
        layout.addWidget(confirm_label)
        layout.addWidget(self.signup_confirm)
        layout.addSpacing(10)
        layout.addWidget(signup_button)
        layout.addSpacing(20)
        layout.addLayout(login_layout)
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def handle_login(self):
        from db import validate_login  # Import here to avoid circular imports
        
        username = self.login_username.text()
        password = self.login_password.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return
        
        if validate_login(username, password):
            self.login_successful.emit(username)
        else:
            QMessageBox.warning(self, "Login Error", "Invalid username or password.")
    
    def handle_signup(self):
        from db import register_user  # Import here to avoid circular imports
        
        username = self.signup_username.text()
        password = self.signup_password.text()
        confirm = self.signup_confirm.text()
        
        if not username or not password or not confirm:
            QMessageBox.warning(self, "Signup Error", "Please fill in all fields.")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Signup Error", "Passwords do not match.")
            return
        
        if register_user(username, password):
            QMessageBox.information(self, "Success", "Account created successfully. You can now log in.")
            self.stacked_widget.setCurrentIndex(0)  # Switch to login page
            self.login_username.setText(username)  # Pre-fill username
            self.login_password.clear()
        else:
            QMessageBox.warning(self, "Signup Error", "Username already exists. Please choose a different one.")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = LoginSignupGUI()
    window.show()
    sys.exit(app.exec_())