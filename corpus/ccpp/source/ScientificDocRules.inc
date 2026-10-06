.. _SciDoc:

Scientific Documentation Rules
==============================

Scientific and technical documents are
important for code maintenance and for fostering understanding among stakeholders.
As such, physics :term:`schemes <scheme>` are required to include scientific documentation in order to be included in the :term:`CCPP`. This
section describes the process used for documenting :term:`parameterizations <parameterization>` in the CCPP.

Doxygen was chosen as a tool for generating human-readable output due to its
built-in functionality with Fortran, its high level of configurability, and its
ability to parse inline comments within the source code. Keeping documentation
with the source itself increases the likelihood that the documentation will be
updated along with the underlying code. Additionally, inline documentation is
amenable to version control.

The purpose of this section is to provide an understanding of how to properly
document a physics scheme using doxygen inline comments in the Fortran code
and metadata information contained in the ``.meta`` files. It covers what kind of
information should be in the documentation, how to mark up the inline comments
so that doxygen will parse them correctly, where to put various comments within
the code, how to include information from the ``.meta`` files,
and how to configure and run doxygen to generate HTML
output. For an example of the HTML rendering of the CCPP Scientific Documentation, see
https://dtcenter.ucar.edu/GMTB/v7.0.0/sci_doc/index.html
Part of this documentation, namely metadata about subroutine arguments, has
functional significance as part of the CCPP infrastructure. The metadata must be
in a particular format to be parsed by Python scripts that “automatically” generate
a :term:`software cap <physics cap>` for a given physics scheme. Although the procedure outlined herein
is not unique, following it will provide a level of continuity with previous
documented schemes.

Reviewing the documentation for CCPP parameterizations is a good way of getting
started in writing documentation for a new scheme.

Doxygen Comments and Commands
-----------------------------

All doxygen commands start with a backslash ("``\``") or an at-sign ("``@``"). The
doxygen inline comment blocks begin with "``!>``", and subsequent lines begin with "``!!``",
which means that regular Fortran comments using "``!``" are not parsed by doxygen.

In the first line of each Fortran file, a brief one-sentence overview of the file's purpose
should be included, using the doxygen command ``\file``:

.. code-block:: console

   !> \file cires_ugwp.F90
   !! This file contains the Unified Gravity Wave Physics (UGWP) scheme by Valery Yudin (University of Colorado, CIRES)

A parameter definition begins with "``!<``", where the "``<``" sign tells
Doxygen that documentation follows. Example:

.. code-block:: console

   integer, parameter, public :: NF_VGAS = 10   !< number of gas species
   integer, parameter         :: IMXCO2  = 24   !< input CO2 data longitude points
   integer, parameter         :: JMXCO2  = 12   !< input CO2 data latitude points
   integer, parameter         :: MINYEAR = 1957 !< earlist year 2D CO2 data available


Doxygen Documentation Style
---------------------------

To document a physics :term:`suite`, a broad array of information should be included
in order to serve both software engineering and scientific purposes. The
documentation style could be divided into four categories:

* Doxygen Files
* Doxygen Pages (overview page and scheme pages)
* Doxygen Modules
* Bibliography

Doxygen files
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Doxygen provides the ``\file`` tag as a way to provide documentation on the level of
Fortran source code files. That is, in the generated documentation,
one may navigate by source code filenames (if desired) rather than through
a “functional” navigation. The most important documentation organization is
through the “module” concept mentioned below, because the division of a scheme
into multiple source files is often functionally irrelevant. Nevertheless,
using a ``\file`` tag provides an alternate path to navigate the documentation
and it should be included in every source file. Therefore, it is prudent to
include a small documentation block to describe what code is in each file
using the ``\file`` tag, e.g.:

.. code-block:: fortran

   !>\file cu_gf_deep.F90
   !! This file is the Grell-Freitas deep convection scheme.

The brief description for each file is displayed next to the source filename
on the doxygen-generated “File List” page:

.. figure:: _static/DoxygenFileList.png
   :align: center

Doxygen Overview Page
^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Pages* in Doxygen can be used for documentation that is not directly attached to a source code
entity such as a file or module. In the context of CCPP they are used for external text files that
generate pages with a high-level scientific overview, typically containing a longer description of
a project or suite. You can refer to any source code entity from within a page.

The DTC maintains a main page, created by the Doxygen command
``\mainpage``, which contains an overall description and background of the CCPP.
Physics developers do not have to edit the file with the mainpage (``mainpage.txt``), which is
formatted like this:

.. code-block:: console

   /**
   \mainpage Introduction
   ...
   */

All other pages listed under the main page are created using the Doxygen
tag ``\page`` described in the next section. In any Doxygen page,
you can refer to any entity of source code by using Doxygen tag ``\ref``
or ``@ref``. Example from ``GFS_v16_suite.txt``:

.. code-block:: console

   /**
   \page GFS_v16_page GFS_v16 Suite 
   
   \section gfsv16_suite_overview Overview
   
   Version 16 of the Global Forecast System (GFS) was implemented operationally by the NOAA
   National Centers for Environmental Prediction (NCEP) in 2021. The GFS_v16 suite uses the parameterizations in the following order:
    - \ref GFS_RRTMG
    - \ref GFS_SFCLYR
    - \ref GFS_NSST
    - \ref GFS_OCEAN
    - \ref GFS_NOAH
    - \ref GFS_SFCSICE
    - \ref GFS_SATMEDMFVDIFQ
    - \ref GFS_UGWP_v0
    - \ref GFS_OZPHYS
    - \ref GFS_H2OPHYS
    - \ref GFS_SAMFdeep
    - \ref GFS_SAMFshal
    - \ref GFDL_cloud
   
   \section sdf_gfsv16b Suite Definition File
   \include  suite_FV3_GFS_v16.xml
   ...
   */

The HTML result of this Doxygen code `can be viewed here <https://dtcenter.ucar.edu/GMTB/v7.0.0/sci_doc/_g_f_s_v16_page.html>`_.
You can see that the ``-`` symbols at the start of a line generate a list with bullets, and the
``\ref`` commands generate links to the appropriately labeled pages. The ``\section`` comands
indicate section breaks, and the ``\include`` commands will include the contents of another file.

Other valid Doxygen commands for style, markup, and other functionality can be found in the `Doxygen documentation <https://doxygen.nl/manual/index.html>`_.

Physics Scheme Pages
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each major scheme in CCPP should have its own scheme page containing an
overview of the parameterization.  These pages are not tied to the Fortran
code directly; instead, they are created with a separate text file that starts
with the command ``\page``.  For CCPP, the stand-alone Doxygen pages, including the main page
and the scheme pages, are contained in the *ccpp-physics* repository, under the
``ccpp-physics/physics/docs/pdftxt/`` directory. Each page (aside from the main page) has a
*label* (e.g., “GFS_SAMFdeep” in the following example) and a
user-visible title (“GFS Scale-Aware Simplified Arakawa-Schubert (sa-SAS) Deep Convection
Scheme” in the following example).  It is noted that labels must be unique
across the entire doxygen project so that the ``\ref`` command can be used
to create an unambiguous link to the structuring element. It therefore makes
sense to choose label names that refer to their context.

.. _doxygen_page_example:
.. code-block:: console

   /**
   \page GFS_SAMFdeep GFS Scale-Aware Simplified Arakawa-Schubert (sa-SAS) Deep Convection Scheme
   \section des_deep Description
    The scale-aware mass-flux (SAMF) deep convection scheme is an
    updated version of the previous Simplified Arakawa-Schubert (SAS) scheme
    with scale and aerosol awareness and parameterizes the effect of deep
    convection on the environment (represented by the model state variables)
    in the following way...
   ...
   \section intra_deep  Intraphysics Communication
   \ref arg_table_samfdeepcnv_run

   \section gen_al_deep General Algorithm
   \ref general_samfdeep

   */


The physics scheme page will often describe the following:

1. A "Description" section, which usually includes:

   * Scientific origin and scheme history
      * External sources and citations can be referenced with ``\cite`` tags
   * Key features and differentiating points compared to other schemes
   * Tables, schematics, other images inserted using the ``\image`` tag
      * To insert images into doxygen documentation, you’ll need to prepare your
        images in a graphical format, such as Portable Network Graphic (png), depending
        on which type of doxygen output you are planning to generate. For example, for LaTeX
        output, the images must be provided in Encapsulated PostScript (.eps), while for
        HTML output the images can be provided in the png format. Images are stored in
        ``ccpp-physics/physics/docs/img`` directory.  Example of including an image for
        HTML output:

        .. code-block:: console

           \image  html  gfdl_cloud_mp_diagram.png "Figure 1: GFDL MP at a glance (Courtesy of S.J. Lin at GFDL)" width=10cm

2. An "Intraphysics Communication" section

   The argument table for CCPP entry point subroutine ``{scheme}_run`` will be in this section.
   It is created by inserting a reference link (``\ref``) to the corresponding Doxygen label in the Fortran code
   for the scheme. In the :ref:`above example <doxygen_page_example>`, the ``\ref arg_table_samfdeepcnv_run``
   tag references the section of Doxygen-annotated source code in `ccpp-physics/physics/CONV/SAMF/samfdeepcnv.f <https://github.com/NCAR/ccpp-physics/blob/da75531/physics/CONV/SAMF/samfdeepcnv.f>`__
   that contains the scheme's argument table as an included html document, as described in the
   :ref:`following section <DoxygenModules>`.

3. A "General Algorithm" section

   The general description of the algorithm will be in this section. It is created by inserting
   a reference link (``\ref``) pointing to the corresponding Doxygen-annotated source code for the scheme,
   as described in the :ref:`following section <DoxygenModules>`.

As can be seen in the above examples, symbols ``/\*\*`` and ``*/`` need to be the first and last entries of the page.

Note that separate pages can also be created to document something that is not a scheme.
For example, a page could be created to describe a suite, or how a set of schemes work
together. Doxygen automatically generates an index of all pages that is visible at the
top-level of the documentation, thus allowing the user to quickly find, and navigate
between, the available pages.

.. _DoxygenModules:

Doxygen Modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The CCPP documentation is based on doxygen modules (note this is not the same as
Fortran modules). Each doxygen module pertains to a particular parameterization and
is used to aggregate all code related to that scheme, even when it is in separate
files. Since doxygen cannot know which files or subroutines belong to each physics
scheme, each relevant subroutine must be tagged with the module name. This allows
doxygen to understand your modularized design and generate the documentation accordingly.
`Here is a list of modules <https://dtcenter.ucar.edu/GMTB/v7.0.0/sci_doc/namespaces.html>`_
defined in CCPP.

A module is defined using:

.. code-block:: console

   !>\defgroup group_name group_title

Where ``group_name`` is the identifier and the ``group_title`` is what the
:term:`group` is referred to in the output. In the example below, we’re defining a parent
module “GFS radsw Main”:

.. code-block:: fortran

   !> \defgroup module_radsw_main GFS radsw Main
   !! This module includes NCEP's modifications of the RRTMG-SW radiation
   !! code from AER.
   !! ...
   !!\author   Eli J. Mlawer, emlawer@aer.com
   !!\author   Jennifer S. Delamere, jdelamer@aer.com
   !!\author   Michael J. Iacono, miacono@aer.com
   !!\author   Shepard A. Clough
   !!\version NCEP SW v5.1  Nov 2012 -RRTMG-SW v3.8
   !!

One or more contact persons should be listed with \author. If you make
significant modifications or additions to a file, consider adding an
\author and a \version line for yourself. The above example generates
the Author, Version sections on the page. All email addresses are converted
to mailto hypertext links automatically:

**Author**
    Eli J. Mlawer, emlawer@aer.com

    Jennifer S. Delamere, jdelamer@aer.com

    Michael J. Iacono, miacono@aer.com

    Shepard A. Clough
**Version**
    NCEP SW v5.1  Nov 2012 -RRTMG-SW v3.8

In order to include other pieces of code in the same module, the following
tag must be used at the beginning of a comment block:

.. code-block:: console

   \ingroup group_name

For example:

.. code-block:: fortran

   !>\ingroup module_radsw_main
   !> The subroutine computes the optical depth in band 16:  2600-3250
   !! cm-1 (low - h2o,ch4; high - ch4)
   !-----------------------------------
         subroutine taumol16
   !...................................

In the same comment block where a group is defined for a physics scheme,
there should be some additional documentation. First, using the ``\brief``
command, a brief one or two sentence description of the scheme should be
included. After a blank doxygen comment line, begin the scheme origin
and history using ``\version``, ``\author`` and ``\date``.

Each subroutine that is a CCPP entry point to a parameterization should
be further documented with a documentation block immediately preceding
its definition in the source. The documentation block should include at
least the following components:

* A brief one- or two-sentence description with the ``\brief`` tag

* A more detailed one or two paragraph description of the function of the subroutine

* A comment indicating that metadata information about the subroutine arguments follows
  (in this example, the subroutine is called ``SUBROUTINE_NAME``.  Note that this line is
  also functional documentation used during the CCPP *prebuild* step.

.. code-block:: fortran

  !! \section arg_table_SUBROUTINE_NAME Argument Table

* A second comment indicating that a table
  of metadata to describe the subroutine arguments will be included from a separate file
  in HTML format (in this case, file ``SUBROUTINE_NAME.html``).
  Please refer to the section below for information on how to generate the HTML files
  with metadata information from the ``.meta`` files.

  The argument table should be immediately followed by a blank doxygen line “!!”.

.. code-block:: fortran

   !! \htmlinclude SUBROUTINE_NAME.html
   !!

* A section called “General Algorithm” with a bullet or numbered list of
  the tasks completed in the subroutine algorithm

* At the end of initial subroutine documentation block, a “Detailed algorithm”
  section is started and the entirety of the code  is encompassed with the
  ``!> @{`` and ``!> @}`` delimiters. This way, any comments explaining detailed
  aspects of the code are automatically included in the “Detailed Algorithm” section.

For subroutines that are not a CCPP entry point to a scheme, no inclusion of
metadata information is required.
But it is suggested that following ``\ingroup`` and ``\brief``, use
``\param`` to define each argument with local name, a short description and unit, i.e.,

.. code-block:: console

   !>  \ingroup HEDMF
   !!  \brief This subroutine is used for calculating the mass flux and updraft properties.
   !!  ...
   !!
   !!  \param[in] im      integer, number of used points
   !!  \param[in] ix      integer, horizontal dimension
   !!  \param[in] km      integer, vertical layer dimension
   !!  \param[in] ntrac   integer, number of tracers
   !!  \param[in] delt    real, physics time step
   !!  ...
   !!  \section general_mfpbl mfpbl General Algorithm
   !!  -# Determine an updraft parcel's entrainment rate, buoyancy, and vertical velocity.
   !!  -# Recalculate the PBL height ...
   !!  -# Calculate the mass flux profile and updraft properties.
   !!  \section detailed_mfpbl mfpbl Detailed Algorithm
   !>  @{
          subroutine mfpbl(im,ix,km,ntrac,delt,cnvflg,                       &
          &   zl,zm,thvx,q1,t1,u1,v1,hpbl,kpbl,                              &
          &   sflx,ustar,wstar,xmf,tcko,qcko,ucko,vcko)
            …
          end subroutine mfpbl
   !>  @}

Bibliography
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Doxygen can handle in-line paper citations and link to an automatically created
bibliography page. The bibliographic data for any papers that are cited need to
be put in BibTeX format and saved in a .bib file. The .bib file for CCPP is
included in the :term:`CCPP Physics` repository (``ccpp-physics/physics/docs/library.bib``),
and the doxygen configuration option ``cite_bib_files`` points to the included file.

Citations are invoked with the following tag:

.. code-block:: console

   \cite bibtex_key_to_paper

Equations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See `the Doxygen documentation <https://www.doxygen.nl/manual/formulas.html>`_ for information
about including equations. For the best rendering, the following option
should be set in the :ref:`Doxygen configuration file <Doxygen_config_file>`:

.. code-block:: console

   USE_MATHJAX            = YES
   MATHJAX_RELPATH        = https://cdn.jsdelivr.net/npm/mathjax@2

There are many great online resources to use the LaTeX math typesetting used in doxygen.

Doxygen Configuration
-----------------------------

.. _Doxygen_config_file:

Configuration File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The CCPP is distributed with a doxygen configuration file
``ccpp-physics/physics/physics/docs/ccpp_doxyfile``, such that you don’t need to
create an additional one.

Doxygen files for layout (``ccpp_dox_layout.xml``), HTML style (``doxygen-awesome-ccpp.css``),
and the bibliography (``library.bib``) are provided with the CCPP. Additionally, a
configuration file is supplied, with the following variables modified from the default:

Diagrams
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On its own, Doxygen is capable of creating simple text-based class diagrams.
With the help of the additional software GraphViz, Doxygen can generate
additional graphics-based diagrams, optionally in Unified Modeling Language (UML) style. To enable
GraphViz support, the configure file parameter ``“HAVE_DOT”`` must be set to ``“YES”``.

You can use doxygen to create call graphs of all the physics schemes in CCPP.
In order to create the call graphs you will need to set the following options in
your doxygen config file:

.. code-block:: console

   HAVE_DOT           	= YES
   EXTRACT_ALL        	= YES
   EXTRACT_PRIVATE    	= YES
   EXTRACT_STATIC     	= YES
   CALL_GRAPH         	= YES

Note that you will need the DOT (graph description language) utility to be installed
when starting doxygen. Doxygen will call it to generate the graphs. On most
distributions the DOT utility can be found in the GraphViz package. Here is
the call graph for subroutine *mpdrv* in GFDL cloud microphysics generated by doxygen:

.. figure:: _static/DoxygenCallGraph.png
   :align: center

Including metadata information
-----------------------------------------------

As described above, a table of metadata information should be included in the documentation
for every CCPP entry point scheme. Before doxygen is run, the table for each scheme must be manually
created in separate files in HTML format, with one file per scheme. The HTML files are included in the
Fortran files using the doygen markup below.

.. code-block:: fortran

   !! \htmlinclude SUBROUTINE_NAME.html
   !!

The tables should be created using a Python script distributed with the :term:`CCPP Framework`,
``ccpp-framework/scripts/metadata2html.py``.

.. note::
   You will need to set the environment variable ``PYTHONPATH`` to include the directories
   ``ccpp/framework/scripts`` and ``ccpp/framework/scripts/parse_tools``. As an example for bash-like shells:

   .. code-block::

      export PYTHONPATH=`pwd`/ccpp/framework/scripts:`pwd`/ccpp/framework/scripts/parse_tools

For the example of the  :term:`SCM`, where both scripts need to be called from the :term:`host model` top-level directory:

.. code-block:: fortran

   ./ccpp/framework/scripts/metadata2html.py -m ccpp/physics/physics/file.meta -o ccpp/physics/physics/docs

where ``-m`` is used to specify a file with metadata information and ``-o`` is used to specify
the directory for output. Note that a single input file (``.meta``) may have more than one CCPP entry point
scheme, and therefore can be used to generate more than one HTML file.

Note that the ``.meta`` files are supplied in the CCPP Physics repository, and that there is a ``.meta`` file for
each Fortran file that contains one or more CCPP entry point scheme. The ``.meta`` files are located in the same
directory as the scheme Fortran files (``ccpp-physics/physics``).

To generate the complete Scientific Documentation, the script ``./ccpp/framework/scripts/metadata2html.py``
must be run separately for each ``.meta`` file available in ``ccpp-physics/physics``. Alternatively, a batch mode exists
that converts all metadata files associated with schemes and variable definitions in the CCPP prebuild config;
again using the SCM as an example:

.. code-block:: fortran

   ./ccpp/framework/scripts/metadata2html.py -c ccpp/config/ccpp_prebuild_config.py

Note that the options ``-c`` and ``-m`` are mutually exclusive, but that one of them is required. The option ``-m`` also requires
the user to specify ``-o``, while the option ``-c`` will ignore ``-o``. For more information, use

.. code-block:: fortran

   ./ccpp/framework/scripts/metadata2html.py --help

Using Doxygen
-------------------------------

In order to generate the doxygen-based documentation, you will need to follow five steps:

#. Have the executables ``doxygen`` (https://doxygen.nl/), ``graphviz`` (https://graphviz.org/),
   and ``bibtex`` (https://www.bibtex.org/) installed on your machine and in your ``PATH``.
   These utilities can be installed on MacOS via `Homebrew <https://brew.sh/>`_, or installed
   manually via the instructions on each utility's page linked above.

#. Document your code, including the doxygen main page, scheme pages, and inline
   comments within the source code as described above.

#. Run ``metadata2html.py`` to create files in HTML format containing metadata
   information for each CCPP entry point scheme.

#. Prepare a Bibliography file in BibTex format for papers or other references cited in the physics suites.

#. Create or edit a doxygen configuration file to control which doxygen pages, source
   files, and bibliography get parsed, in addition to how the source files get parsed, and to
   customize the output.

#. Run doxygen from the directory ``ccpp/physics/physics/docs`` using the command line
   to specify the doxygen configuration file as an argument. For the CCPP Scientific documentation,
   this file is called ``ccpp_doxyfile``:

  ``doxygen ccpp_doxyfile``

  Running this command may generate warnings or errors that need to be fixed
  in order to produce proper output. The location and type of output
  (HTML, LaTeX, etc.) are specified in the configuration file.
  The generated HTML documentation can be viewed by pointing an HTML
  browser to the ``index.html`` file in the ``./docs/doc/html/`` directory.

For precise instructions or other help creating the scientific documentation, visit the CCPP GitHub discussions
page at https://github.com/NCAR/ccpp-physics/discussions
