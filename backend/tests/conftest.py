import sys
import os

# Add backend root to Python path so 'app' module is always found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
