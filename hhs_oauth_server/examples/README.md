# EXAMPLES

The examples folder contains examples of custom environment files.

To use these files:
1. Copy to the _start.settings folder
2. update the values in the file to match your individual settings for the environment

Use these custom settings files to store sensitive information and keys for your environment.

Do not include the custom files in _start.settings in the git repository.

# Custom Settings

To apply a custom settings file see the examples in:
- hhs_ouath_server/settings.

The Typical approach is to:

- Create a settings file that inherits values from base.py.
- Configure any values in your custom settings that you want to override the values set in base.
- Set the DJANGO_SETTINGS_MODULE environment variable to point to your new settings file.
- Restart your server to activate the new settings.
 