"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['pilcrow.py']
DATA_FILES = []
OPTIONS = {
		'iconfile': 'logo.icns',
    'packages': ["PyQt5", "qt_material", "cffsubr","jinja2", "PIL", "cffsubr"],
'plist': {
        'CFBundleIdentifier': 'uk.co.corvelsoftware.Pilcrow',
    }
}
setup(
    app=APP,
    name="Pilcrow",
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
