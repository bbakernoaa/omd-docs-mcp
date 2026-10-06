.. include:: prolog.inc

How to Use this Document
========================

This document contains documentation for the Common Community Physics Package (:term:`CCPP`). It describes the

* :term:`Primary physics schemes <primary scheme>` and :term:`interstitials <interstitial scheme>`
* :term:`Suite definition files <SDF>`
* CCPP-compliant :term:`parameterizations <parameterization>`
* Process to add a new scheme or suite
* Host-side coding
* CCPP code management and governance
* Parameterization-specific output
* Debugging strategies

The following table describes the type changes and symbols used in this guide.

.. list-table:: *Type changes and symbols used in this guide.*
   :header-rows: 1

   * - Typeface or Symbol
     - Meaning
     - Examples
   * - ``AaBbCc123``
     -
         * The names of commands, files, and directories
         * On-screen terminal output
     -
         * Edit your ``.bashrc`` file
         * Use ``ls -a`` to list all files.
         * ``host$ You have mail!``
   * - *AaBbCc123*
     -
         * The names of CCPP-specific terms, subroutines, etc.
         * Captions for figures, tables, etc.
     -
         * Each scheme must include at least one of the following subroutines: ``{schemename}_timestep_init``, ``{schemename}_init``, ``{schemename}_run``, ``{schemename}_finalize``, and ``{schemename}_timestep_finalize``.
         * *Listing 2.1: Fortran template for a CCPP-compliant scheme showing the* _run *subroutine.*
   * - **AaBbCc123**
     - Words or phrases requiring particular emphasis
     - Fortran77 code should **not** be used

Following these typefaces and conventions, shell commands, code examples, namelist variables, etc.
will be presented in this style:

.. code-block:: console

   mkdir ${TOP_DIR}

Some CCPP-specific terms will be highlighted using *italics*, and words requiring particular emphasis will be highlighted in **bold** text.

In some places there are helpful asides or warnings that the user should pay attention to; these
will be presented in the following style:

.. note::
   This is a helpful aside that may or may not be relevant to your specific use case.

.. warning::
   This is an important point that should **not** be ignored!


In several places in the technical documentation, we need to refer to locations of files or directories in the source code. Since the directory structure depends on the :term:`host model`, in particular the directories where the ``ccpp-framework`` and ``ccpp-physics`` source code is checked out, and the directory from which the ``ccpp_prebuild.py`` code generator is called, we use the following convention:

1. When describing files relative to the ``ccpp-framework`` or ``ccpp-physics`` top-level, without referring to a specific model, we use ``ccpp-framework/path/to/file/A`` and ``ccpp-physics/path/to/file/B``.
2. When describing specific tasks that depend on the directory structure within the host model, for example how to run ``ccpp_prebuild.py``, we explicitly mention the host model and use its directory structure relative to the top-level directory. For the example of the :term:`SCM`: ``./ccpp/framework/path/to/file/A``.

