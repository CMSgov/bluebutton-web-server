# Transparent Health Extensible Skin (the_skin)

This folder and it's companion sitestatic sub-folder represent the assets
used for the default Transparent Health Extensible skin/theme for the OAuth2 
Engine.

## How is the_skin implemented?

### base.py settings file
base.py has a setting:

ENGINE_SKIN = 'the_skin' + '/'

This value can be overridden in an alternative settings file that imports 
from base.py.

The trailing slash is important because the variable will typically be used in
a file or folder specification and the trailing slash is the folder delimiter.

The ENGINE_SKIN variable is added to SETTINGS_EXPORT in base.py. This enables 
the value of ENGINE_SKIN to be accessed in Templates by using the format:

{{ settings.ENGINE_SKIN }}

### TEMPLATES definition in base.py

The ENGINE_SKIN variable is then used in the TEMPLATES dict DIRS setting 
and a builtins list is added to define a templatetag:

    TEMPLATES = [
        {
            
            'DIRS': [os.path.join(BASE_DIR, ENGINE_SKIN+'templates')],
            'builtins': ['apps.home.templatetags.engine_skin',],
        },
    ]

The engine_skin.py file defines a simple_tag: skin_static.

The skin_static tag is loaded into a template using the following setting:

    {% load engine_skin %}
    
Use {% skin_static 'filename' %} in the template to replace {% static %} 
references.

    

    
### Adding a TemplateTag to handle static references

    TEMPLATES = [
        {
            
           'DIRS': [os.path.join(BASE_DIR, ENGINE_SKIN+'templates')],        
           
 


All of the assets used to implement the_skin are then placed in a matching 
named folder in sitestatic and templates.

## How do I create my own theme?

You can create your own skin as follows:

    1. Decide on a skin name that can be used as a folder name (avoid spaces etc.)
    2. Copy the sitestatic/the_skin folder to a new folder under sitestatic
    3. Copy the templates/the_skin folder to a new folder under templates
    4. update ENGINE_SKIN in settings to reflect the new folder name
    5. Edit the files in your new folders to apply the style and UI you want.
    6. When you reference files in your skin folders remember to include the
    ENGINE_SKIN variable in the file reference.
    
    

