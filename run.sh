#!/bin/bash
export PYTHONPATH=/var/www/engineering_system
export DJANGO_SETTINGS_MODULE=engineering_system.settings
cd /var/www/engineering_system
/usr/bin/python3.12 -c "
import os, sys
sys.path.insert(0, '/var/www/engineering_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engineering_system.settings')
import django
django.setup()
from django.core.management import execute_from_command_line
# Prepend 'manage.py' so execute_from_command_line works correctly
execute_from_command_line(['manage.py'] + sys.argv[1:])
" "$@"
