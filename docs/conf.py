# -*- coding: utf-8 -*-
#
# SportsLabKit documentation build configuration file, created by
# sphinx-quickstart.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import os
import sys

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(".."))

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "autoapi.extension",
    'sphinxcontrib.gtagjs',
    "myst_nb",
    "sphinx_copybutton",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# -- Options for autoapi -------------------------------------------------------

autoapi_dirs = ["../sportslabkit"]
autoapi_type = "python"

autoapi_template_dir = "_templates/autoapi"

autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]

autoapi_keep_files = True
autoapi_add_toctree_entry = False


#
# -- Options for TODOs -------------------------------------------------------
#
todo_include_todos = True

# The suffix of source filenames.
source_suffix = [".md", ".rst"]

# The encoding of source files.
# source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "SportsLabKit"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = "0.1"
# The full version, including alpha/beta/rc tags.
release = "0.1"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
# language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
# today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

# The reST default role (used for this markup: `text`) to use for all documents.
# default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# A list of ignored prefixes for module index sorting.
# modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "furo"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "sidebar_hide_name": False,
    "dark_css_variables": {
        "color-brand-primary": "#0097A7",
        "color-brand-content": "#0097A7",
        "color-background-secondary": "#212528",
    }
    # "icon_links": [
    #     {
    #         "name": "Github",
    #         "url": "https://github.com/AtomScott/SportsLabKit",
    #         "icon": "fab fa-github-square",
    #     },
    #     {
    #         "name": "Twitter",
    #         "url": "https://twitter.com/AtomJamesScott",
    #         "icon": "fab fa-twitter-square",
    #     },
    # ],
    # "use_edit_page_button": False,
}

# Add any paths that contain custom themes here, relative to this directory.
# html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
# html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "_static/logo.png"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
# html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    "**": [
        "sidebar/scroll-start.html",
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/navigation.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
    ]
}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
# html_domain_indices = True

# If false, no index is generated.
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, links to the reST sources are added to the pages.
# html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
# html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
# html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = "sportslabkitdoc"


# -- Options for LaTeX output --------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    # 'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
    ("index", "sportslabkit.tex", "SportsLabKit Documentation", "Atom Scott", "manual"),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# If true, show page references after internal links.
# latex_show_pagerefs = False

# If true, show URL addresses after external links.
# latex_show_urls = False

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_domain_indices = True


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [("index", "sportslabkit", "SportsLabKit Documentation", ["Atom Scott"], 1)]

# If true, show URL addresses after external links.
# man_show_urls = False


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "sportslabkit",
        "SportsLabKit Documentation",
        "Atom Scott",
        "SportsLabKit",
        "A short description of the project.",
        "Miscellaneous",
    ),
]

# Documents to append as an appendix to all manuals.
# texinfo_appendices = []

# If false, no module index is generated.
# texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
# texinfo_show_urls = 'footnote'

# -- Options for autodoc -------------------------------------------------------
autoclass_content = "both"

# descriptions of the relevant function/method.
autodoc_typehints = "signature"

# Don't show class signature with the class' name.
autodoc_class_signature = "separated"

autodoc_mock_imports = [
    # I think the imports should be `as imported`. For example, `sklean` instead
    # of `scikit-learn`.
    "joblib",
    "numpy",
    "matplotlib",
    "mplsoccer",
    "opencv_python",
    "pandas",
    "Pillow",
    "podm",
    "scikit-learn",
    "setuptools",
    "tqdm",
    "vidgear",
    "cv2",
    "torch",
    "omegaconf",
    "more_itertools",
    "sklearn",
]

# -- Options for Google Analytics ---------------------------------------------

gtagjs_ids = [
    "G-GXSVPS0MXS",
]


# -- Options for intersphinx ---------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    "sklearn": ("https://scikit-learn.org/stable", None),
    "matplotlib": ("https://matplotlib.org", None),
    "pillow": ("https://pillow.readthedocs.io/en/stable/", None),
    "vidgear": ("https://abhitronix.github.io/vidgear/latest/", None),
    "torch": ("https://pytorch.org/docs/stable/", None),
    "omegaconf": ("https://omegaconf.readthedocs.io/en/latest/", None),
    "more_itertools": ("https://more-itertools.readthedocs.io/en/stable/", None),
    "mypy": ("https://mypy.readthedocs.io/en/stable/", None),
}
# -- custom auto_summary() macro ---------------------------------------------


def contains(seq, item):
    """Jinja2 custom test to check existence in a container.
    Example of use:
    {% set class_methods = methods|selectattr("properties", "contains", "classmethod") %}
    Related doc: https://jinja.palletsprojects.com/en/3.1.x/api/#custom-tests
    """
    return item in seq


def prepare_jinja_env(jinja_env) -> None:
    """Add `contains` custom test to Jinja environment."""
    jinja_env.tests["contains"] = contains


autoapi_prepare_jinja_env = prepare_jinja_env

# Custom role for labels used in auto_summary() tables.
rst_prolog = """
.. role:: summarylabel
"""

# Related custom CSS
html_css_files = [
    "css/label.css",
]

# noinspection PyUnusedLocal
def autoapi_skip_members(app, what, name, obj, skip, options):
    # skip submodules
    if what == "module":
        skip = True
    elif what == "data":
        if obj.name in ["EASING_FUNCTIONS", "ParamType"]:
            skip = True
    elif what == "function":
        if obj.name in ["working_directory"]:
            skip = True
    return skip


def setup(app):
    app.connect("autoapi-skip-member", autoapi_skip_members)
