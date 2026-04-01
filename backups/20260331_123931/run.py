#!/usr/bin/env python
import os, sys
sys.path.insert(0, '/var/www/engineering_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engineering_system.settings')
from django.core.management import execute_from_command_line
execute_from_command_line(sys.argv)
