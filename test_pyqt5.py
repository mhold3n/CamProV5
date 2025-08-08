"""
Simple script to test if PyQt5 is installed and working correctly.
This script creates a basic window to verify that PyQt5 can display a GUI.
"""

import sys

try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
    from PyQt5.QtCore import Qt
    
    print("PyQt5 is installed correctly.")
    
    # Create a basic application and window
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("PyQt5 Test")
    window.setGeometry(100, 100, 400, 200)
    
    # Create central widget and layout
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    
    # Add a label
    label = QLabel("PyQt5 is working correctly!")
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("font-size: 18px; color: green;")
    layout.addWidget(label)
    
    # Add instructions
    instructions = QLabel("If you can see this window, PyQt5 is installed correctly.\nClose this window to continue.")
    instructions.setAlignment(Qt.AlignCenter)
    layout.addWidget(instructions)
    
    # Show the window
    window.show()
    
    # Start the event loop
    print("Displaying test window. Close the window to continue.")
    sys.exit(app.exec_())
    
except ImportError:
    print("PyQt5 is not installed. Please install it using: pip install PyQt5")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)