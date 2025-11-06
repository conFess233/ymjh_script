import sys
import threading
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QProgressBar,
                               QTextEdit, QGroupBox, QFormLayout, QSpinBox, 
                               QDoubleSpinBox, QComboBox, QScrollArea)
from PySide6.QtCore import QTimer, Qt, Signal, QObject
from PySide6.QtGui import QFont, QPalette, QColor

# Import your task classes
from tasks.template_maching_task import TemplateMatchingTask
from tasks.ri_chang_fu_ben import RiChangFuBen
from tasks.lun_jian import LunJian

