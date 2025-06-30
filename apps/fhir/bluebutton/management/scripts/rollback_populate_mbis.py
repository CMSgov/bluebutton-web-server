#!/usr/bin/env python
"""
Rollback script for populate_mbis.py
This script can restore the crosswalk table from a backup file.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hhs_oauth_server.settings.dev_local')
django.setup()

from django.core.management import execute_from_command_line
from apps.fhir.bluebutton.models import Crosswalk

def rollback_from_backup(backup_file):
    """
    Rollback changes by restoring from a backup file
    """
    if not os.path.exists(backup_file):
        print(f"Error: Backup file {backup_file} not found!")
        return False
    
    print(f"Restoring from backup: {backup_file}")
    
    # Use Django's loaddata command
    execute_from_command_line(['manage.py', 'loaddata', backup_file])
    
    print("Rollback completed successfully!")
    return True

def rollback_specific_users(user_ids, old_mbi_values):
    """
    Rollback specific users to their old MBI values
    user_ids: list of user IDs to rollback
    old_mbi_values: dict mapping user_id to old MBI value
    """
    print(f"Rolling back {len(user_ids)} users...")
    
    for user_id in user_ids:
        try:
            user = User.objects.get(username=user_id)
            crosswalk = user.crosswalk
            old_mbi = old_mbi_values.get(user_id)
            
            if old_mbi is not None:
                crosswalk.unhashed_mbi = old_mbi
                crosswalk.save(update_fields=['unhashed_mbi'])
                print(f"Rolled back user {user_id}: MBI -> '{old_mbi}'")
            else:
                print(f"No backup MBI found for user {user_id}")
                
        except User.DoesNotExist:
            print(f"User {user_id} not found")
        except Exception as e:
            print(f"Error rolling back user {user_id}: {e}")

def show_rollback_options():
    """
    Show available rollback options
    """
    print("Rollback Options:")
    print("1. Restore from backup file")
    print("2. Rollback specific users")
    print("3. Show recent changes")
    print("4. Exit")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Rollback populate_mbis changes')
    parser.add_argument('--backup-file', type=str, help='Backup file to restore from')
    parser.add_argument('--user-ids', nargs='+', help='Specific user IDs to rollback')
    parser.add_argument('--old-mbis', nargs='+', help='Old MBI values corresponding to user IDs')
    
    args = parser.parse_args()
    
    if args.backup_file:
        rollback_from_backup(args.backup_file)
    elif args.user_ids and args.old_mbis:
        if len(args.user_ids) != len(args.old_mbis):
            print("Error: Number of user IDs must match number of old MBI values")
        else:
            old_mbi_dict = dict(zip(args.user_ids, args.old_mbis))
            rollback_specific_users(args.user_ids, old_mbi_dict)
    else:
        show_rollback_options() 