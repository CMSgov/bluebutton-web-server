from getenv import env

""" theme selection """

DEFAULT_THEME = 0
THEME_SELECTED = DEFAULT_THEME

THEMES = {
    0: {
        'NAME': 'Default-Readable',
        'PATH': 'theme/default/',
        'INFO': 'Readable san-serif base theme',
    },
    3: {
        'NAME': 'Readable',
        'PATH': 'theme/readable/',
        'INFO': 'Easy to read Bootswatch Theme',
    },
    4: {
        'NAME': 'Cerulean',
        'PATH': 'theme/cerulean/',
        'INFO': 'Blue Bootswatch theme theme',
    },
    5: {
        'NAME': 'Cosmo',
        'PATH': 'theme/cosmo/',
        'INFO': 'Cosmo bootswatch theme',
    },
    6: {
        'NAME': 'Cyborg',
        'PATH': 'theme/cyborg/',
        'INFO': 'Cyborg bootswatch theme',
    },
    7: {
        'NAME': 'Darkly',
        'PATH': 'theme/darkly/',
        'INFO': 'Darkly bootswatch theme',
    },
    8: {
        'NAME': 'Flatly',
        'PATH': 'theme/flatly/',
        'INFO': 'Flatly bootswatch theme',
    },
    9: {
        'NAME': 'Journal',
        'PATH': 'theme/journal/',
        'INFO': 'Journal bootswatch theme',
    },
    10: {
        'NAME': 'Lumen',
        'PATH': 'theme/lumen/',
        'INFO': 'Lumen bootswatch theme',
    },
    11: {
        'NAME': 'Paper',
        'PATH': 'theme/paper/',
        'INFO': 'Paper bootswatch theme',
    },
    12: {
        'NAME': 'Sandstone',
        'PATH': 'theme/sandstone/',
        'INFO': 'Sandstone bootswatch theme',
    },
    13: {
        'NAME': 'Simplex',
        'PATH': 'theme/simplex/',
        'INFO': 'Simplex bootswatch theme',
    },
    14: {
        'NAME': 'Slate',
        'PATH': 'theme/slate/',
        'INFO': 'Slate bootswatch theme',
    },
    15: {
        'NAME': 'Spacelab',
        'PATH': 'theme/spacelab/',
        'INFO': 'Spacelab bootswatch theme',
    },
    16: {
        'NAME': 'Superhero',
        'PATH': 'theme/superhero/',
        'INFO': 'Superhero bootswatch theme',
    },
    17: {
        'NAME': 'United',
        'PATH': 'theme/united/',
        'INFO': 'United bootswatch theme',
    },
    18: {
        'NAME': 'Yeti',
        'PATH': 'theme/yeti/',
        'INFO': 'Yeti bootswatch theme',
    },
    'SELECTED': env('DJANGO_SELECTED_THEME', DEFAULT_THEME),
}

if THEMES['SELECTED'] in THEMES:
    THEME_SELECTED = THEMES['SELECTED']

