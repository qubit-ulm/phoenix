# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
import os

sys.path.insert(0, os.path.abspath("../"))

project = 'PHOENIX'
copyright = '2024, Matthias Kost'
author = 'Matthias Kost'
release = '2024'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx.ext.napoleon",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_static_path = ['_static']


# generate autosummary even if no references
autosummary_generate = True
autosummary_imported_members = True

autodoc_typehints = "description"  # none | description
autodoc_member_order = "bysource"
add_module_names = False
toc_object_entries = True
toc_object_entries_show_parents = "hide"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "nature"
html_css_files = ["phoenix.css"]
html_logo = "_static/phoenix-wordmark.png"
html_favicon = "_static/phoenix-mark.png"

# html_static_path = ["_static"]
