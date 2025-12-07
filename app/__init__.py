# app/__init__.py
import os
import sys

# Ayudar a Python a encontrar módulos
package_dir = os.path.dirname(os.path.abspath(__file__))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)
