import logging
import requests
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from apps.fhir.bluebutton.models import Crosswalk
from django.contrib.auth.models import User
from apps.mymedicare_cb.authorization import OAuth2ConfigSLSx
from apps.mymedicare_cb.validators import is_mbi_format_valid, is_mbi_format_synthetic
from apps.fhir.bluebutton.models import hash_mbi
from django.conf import settings

class Command(BaseCommand):
    help = 'Make API calls to SLSx for each user_id in crosswalk table to get and validate MBI data using OAuth2 tokens.'

    def add_arguments(self, parser):
        parser.add_argument('--logfile', type=str, default='populate_mbis.log', help='Path to log file')
        parser.add_argument('--auth-token', type=str, required=True, help='OAuth2 auth token to use for API calls')
        parser.add_argument('--backup-file', type=str, help='Backup file to create before making changes')
        parser.add_argument('--no-backup', action='store_true', help='Skip creating backup before making changes')

    def create_backup(self, backup_file=None):
        """
        Create a backup of the crosswalk table before making changes
        """
        if backup_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f'crosswalk_backup_{timestamp}.json'
        
        self.stdout.write(f"Creating backup: {backup_file}")
        
        # Get all crosswalk records
        crosswalks = Crosswalk.objects.all()
        
        backup_data = []
        for crosswalk in crosswalks:
            backup_data.append({
                'model': 'apps.fhir.bluebutton.Crosswalk',
                'pk': crosswalk.id,
                'fields': {
                    'user_id': crosswalk.user_id,
                    'fhir_id': crosswalk.fhir_id,
                    'user_hicn_hash': crosswalk.user_hicn_hash,
                    'user_mbi_hash': crosswalk.user_mbi_hash,
                    'mbi': crosswalk.mbi,
                    'user_id_type': crosswalk.user_id_type,
                }
            })
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        self.stdout.write(self.style.SUCCESS(f"Backup created: {backup_file}"))
        return backup_file

    def get_user_info_with_oauth2_token(self, user_id, auth_token, request=None):
        """
        Make API call to SLSx userinfo endpoint using OAuth2 token authentication.
        This mimics the get_user_info method using a provided auth token.
        Focuses only on MBI data, ignoring HICN.
        """
        # Create OAuth2ConfigSLSx instance to get endpoints
        slsx_client = OAuth2ConfigSLSx({'username': user_id})
        
        # Set the auth token (this is what would normally come from exchange_for_access_token)
        slsx_client.auth_token = auth_token
        
        # Set up headers similar to get_user_info
        headers = slsx_client.slsx_common_headers(request)
        headers.update(slsx_client.auth_header())  # This adds "Authorization: Bearer <token>"
        
        # Make API call using OAuth2 Bearer token
        response = requests.get(
            slsx_client.userinfo_endpoint + "/" + user_id,
            headers=headers,
            allow_redirects=False,
            verify=slsx_client.verify_ssl_internal,
        )
        
        # Set status code like in get_user_info
        slsx_client.userinfo_status_code = response.status_code
        response.raise_for_status()

        # Get data.user part of response (same as get_user_info)
        data_user_response = response.json().get("data", {}).get("user", None)

        # Validate response like in get_user_info
        if data_user_response is None or data_user_response.get("id", None) is None:
            raise Exception("SLSx userinfo response missing user data")
        
        if user_id != data_user_response.get("id", None):
            raise Exception("SLSx userinfo user_id mismatch")

        # Process user_id like in get_user_info
        slsx_client.user_id = slsx_client.user_id.strip()

        # Process MBI like in get_user_info (only MBI, ignore HICN)
        slsx_client.mbi = data_user_response.get("mbi")
        if slsx_client.mbi is not None and isinstance(slsx_client.mbi, str):
            slsx_client.mbi = slsx_client.mbi.strip().upper()

        # If MBI returned from SLSx is blank, set to None for hash logging
        if slsx_client.mbi == "":
            slsx_client.mbi = None

        # Validate only MBI-related requirements (ignore HICN validation)
        if slsx_client.user_id == "":
            raise Exception("User info sub cannot be empty")
        if slsx_client.mbi is not None and not isinstance(slsx_client.mbi, str):
            raise Exception("User info MBI must be str.")

        # Apply MBI validation like in get_user_info
        slsx_client.mbi_format_synthetic = is_mbi_format_synthetic(slsx_client.mbi)
        slsx_client.mbi_format_valid, slsx_client.mbi_format_msg = is_mbi_format_valid(slsx_client.mbi)

        # Calculate MBI hash like in get_user_info
        slsx_client.mbi_hash = hash_mbi(slsx_client.mbi)

        return slsx_client.mbi, slsx_client.mbi_format_valid, slsx_client.mbi_format_msg, slsx_client.mbi_format_synthetic

    def handle(self, *args, **options):
        logfile = options['logfile']
        auth_token = options['auth_token']
        backup_file = options['backup_file']
        no_backup = options['no_backup']
        
        logger = logging.getLogger('populate_mbis')
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Create backup before making changes (unless --no-backup is specified)
        if not no_backup:
            backup_file = self.create_backup(backup_file)
            logger.info(f"Backup created: {backup_file}")
        else:
            self.stdout.write(self.style.WARNING("Skipping backup creation (--no-backup specified)"))

        updated = 0
        total = 0
        api_calls_made = 0
        
        self.stdout.write(self.style.SUCCESS("Starting API calls to SLSx for all user_ids in crosswalk table using OAuth2 token..."))
        
        for crosswalk in Crosswalk.objects.all():
            total += 1
            user_id = crosswalk.user_id  # Use the user_id column directly
            
            try:
                # Make actual API call to SLSx for this user_id using OAuth2 token
                mbi, is_valid, validation_msg, is_synthetic = self.get_user_info_with_oauth2_token(user_id, auth_token, request=None)
                api_calls_made += 1
                
                if mbi:
                    # Update the crosswalk with the MBI from API
                    old_mbi = crosswalk.mbi
                    crosswalk.mbi = mbi
                    crosswalk.save(update_fields=['mbi'])
                    updated += 1
                    msg = f"API call successful for user {user_id} (Crosswalk ID {crosswalk.id}): '{old_mbi}' -> '{mbi}' (Valid: {is_valid}, Synthetic: {is_synthetic})"
                    logger.info(msg)
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    msg = f"API call successful for user {user_id} (Crosswalk ID {crosswalk.id}): No MBI returned from SLSx"
                    logger.warning(msg)
                    self.stdout.write(self.style.WARNING(msg))
                    
            except Exception as e:
                msg = f"API call failed for user {user_id} (Crosswalk ID {crosswalk.id}): {e}"
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))
                
        summary = f"Processed {total} Crosswalk records. Made {api_calls_made} API calls. Updated {updated} records. Log written to {logfile}."
        if not no_backup:
            summary += f" Backup created: {backup_file}"
        logger.info(summary)
        self.stdout.write(self.style.SUCCESS(summary)) 