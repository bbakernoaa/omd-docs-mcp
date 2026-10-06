.. _CompliantPhysParams:

****************************************
CCPP-Compliant Physics Parameterizations
****************************************

The rules for a :term:`scheme` to be considered :term:`CCPP`-compliant are summarized in this section. It
should be noted that making a scheme CCPP-compliant is a necessary but not guaranteed step
for the acceptance of the scheme in the pool of supported :term:`CCPP Physics`. Acceptance is
dependent on scientific innovation, demonstrated value, and compliance with the rules
described below. The criteria for acceptance of a scheme into the CCPP is under development.

It is recommended that :term:`parameterizations <parameterization>` be comprised of the smallest units that will be used independently.
For example, if a given pair of deep and shallow convection schemes will always be called together
and in a pre-established order, it is acceptable to group them within a single scheme. However, if one
envisions that the deep and shallow convection schemes may someday operate independently, it is
recommended to code two separate schemes to allow more flexibility.

Some schemes in the CCPP have been implemented using a driver as an entry point. In this context,
a driver is defined as a wrapper of code around the actual scheme, providing the CCPP entry
points. In order to minimize the layers of code in the CCPP, the implementation of a driver is
discouraged, that is, it is preferable that the CCPP be composed of atomic parameterizations. 

The implementation of a driver is reasonable under the following circumstances:

* To preserve schemes that are also distributed outside of the CCPP. For example, the Thompson
  microphysics scheme is distributed both with the Weather Research and Forecasting (WRF) model
  and with CCPP. Having a driver with CCPP directives allows the Thompson scheme to remain
  intact so that it can be synchronized between the WRF model and the CCPP distributions. You
  can view this driver module in `ccpp-physics/physics/MP/Thompson/mp_thompson.F90 <https://github.com/NCAR/ccpp-physics/blob/da75531/physics/MP/Thompson/mp_thompson.F90>`__.

* To perform array transformations, such as flipping the vertical direction
  or rearranging the index order: for example, in the subroutine ``gfdl_cloud_microphys_run``
  in `ccpp-physics/physics/gfdl_cloud_microphys.F90 <https://github.com/NCAR/ccpp-physics/blob/da75531/physics/MP/GFDL/gfdl_cloud_microphys.F90>`__.

Schemes in the CCPP are classified into two categories: :term:`primary schemes <primary scheme>` and :term:`interstitial schemes <interstitial scheme>`.
A *primary* scheme is one that produces tendencies of state variables and tracers. These tendencies are then used to update the state by subsequent interstitial scheme(s), or directly by the host model. Updating of the state variables should not occur within primary schemes. Please follow the following guidelines when creating a primary scheme:

* All state variables provided to a CCPP primary scheme should be defined with intent IN.

* State variable tendencies should be provided by the CCPP primary scheme with intent OUT.

*Interstitial* schemes are modularized pieces of code that can be used to update the host's prognostic state variables, 
perform data preparation, compute diagnostics, or other coupling functions, and allow primary schemes to work
together as a :term:`suite`. They can be categorized as “scheme-specific” or “suite-level”. Scheme-specific
interstitial schemes augment a specific primary scheme (to provide additional functionality).
Suite-level interstitial schemes provide additional functionality on top of a class of primary schemes,
connect two or more schemes together, or provide code for conversions, initializing sums, or applying
tendencies, for example. The rules and guidelines provided in the following sections apply both to
primary and interstitial schemes.

CCPP-compliant physics parameterizations are broken down into one or more of the following five :term:`phases <phase>`:

* The *register* phase, which performs actions needed before the host model grid information is known. 
  Examples include querying other model components for information describing the active constituents, along with allocating internal variables needed by the CCPP framework.
  Internal CCPP framework variables are dimensioned by the number of instances, which is set by the host. Detailed instructions for handling multiple CCPP instances are coming soon.
* The *init* phase, which performs actions needed to set up the scheme before the model integration
  begins. Examples of actions needed in this phase include the reading/computation of
  lookup tables, setting of constants (as described in :numref:`Section %s <UsingConstants>`), etc.
* The *timestep_init* phase, which performs actions needed at the start of each physics timestep.
  Examples of actions needed in this phase include updating of time-based settings (e.g. solar angle),
  reading lookup table values, etc.
* The *run* phase, which is the main body of the scheme. Here is where the physics is integrated
  forward to the next timestep.
* The *timestep_final* phase, which performs post-integration calculations such as computing
  statistics or diagnostic tendencies. Not currently used by any scheme.
* The *final* phase, which performs cleanup and finalizing actions at the end of model integration.
  Examples of actions needed in this phase include deallocating variables, closing files, etc.

The various phases have different rules when it comes to parallelization, especially with regards
to how data is blocked among parallel processes; see :numref:`Section %s <ParallelProgramming>`
for more information.

.. _GeneralRules:

General Rules
=============
A CCPP-compliant scheme is written in the form of Fortran modules. Each scheme must be in its own module, and must include at least one of the
following subroutines (*entry points*): *_register*, *_init*, *_timestep_init*, *_run*, *_timestep_final*,
and *_final*. Each subroutine corresponds to one of the six *phases* of the :term:`CCPP Framework` as described above.
The *_run* subroutine contains the code to execute the scheme. If subroutines *_timestep_init* or *_timestep_final* are present,
they will be executed at the beginning and at the end of the :term:`host model` physics timestep,
respectively. If subroutine *_register* is present, it will be called by the host-model BEFORE
calling any other the CCPP phases. Further, if present, the *_init* and *_final* subroutines
associated with a scheme are run at the beginning and at the end of the model run.
The *_init* and *_final* subroutines may be called more than once depending
on the host model’s parallelization strategy, and as such must be idempotent (the answer
must be the same when the subroutine is called multiple times). This can be achieved
by using a module variable ``is_initialized`` that keeps track whether a scheme has been
initialized or not.


:ref:`Listing 2.1 <scheme_template>` contains a template for a CCPP-compliant scheme, which
includes the *_run* subroutine for an example *scheme_template* scheme. Each ``.F`` or ``.F90``
file that contains one or more entry point for a CCPP scheme must be accompanied by a .meta file in the
same directory as described in :numref:`Section %s <MetadataRules>`

.. _scheme_template:
.. literalinclude:: ./_static/scheme_template.F90
   :language: fortran
   :lines: 10-48

*Listing 2.1: Fortran template for a CCPP-compliant scheme showing the _run subroutine. The structure for the other phases (*\ _register, _timestep_init, _init, _final, *and* _timestep_final\ *) is identical.*

The three lines in the example template beginning ``!> \section`` are required. They begin with `!` and so will be treated as comments by the Fortran compiler, but are interpreted by Doxygen
as part of the process to create scientific documentation. Those lines specifically insert an external file containing metadata
information (in this case, ``scheme_template_run.html``) in the documentation. See more on this topic in
:numref:`Section %s <SciDoc>`.

All external information required by the scheme must be passed in via the argument list, including physical constants. Statements
such as ``use EXTERNAL_MODULE`` should not be used for passing in any data.
See :numref:`Section %s <UsingConstants>` for more information on
how to use physical constants.

Note that :term:`standard names <standard name>`, variable names, module names, scheme names and subroutine names are all case insensitive.

Interstitial modules (*schemename_pre* and *schemename_post*) can be included if any part of the
physics scheme must be executed sequentially before (*_pre*) or after (*_post*) the scheme, but
can not be included in the scheme itself (e.g., for including host-specific code).

.. _MetadataRules:

Metadata Table Rules
====================

Each CCPP-compliant physics scheme (``.F`` or ``.F90`` file) must have a corresponding metadata file (``.meta``)
that contains information about CCPP entry point schemes and their dependencies.  These files
contain two types of metadata tables: ``ccpp-table-properties`` and ``ccpp-arg-table``, both of which are mandatory.
The contents of these tables are described in the sections below.

Metadata files (``.meta``) are in a relaxed config file format and contain metadata
for one or more CCPP entry points.

ccpp-table-properties
---------------------
The ``[ccpp-table-properties]`` section is required in every metadata file and has four valid entries:

#. ``type``:  In the CCPP Physics, ``type`` can be ``scheme``, ``module``, or ``ddt`` (derived data type) and must match the
   ``type`` in the associated ``[ccpp-arg-table]`` section(s).

#. ``type``:  In the Host model, ``type`` can be ``host``, ``control``, or ``ddt`` (derived data type) and must match the
   ``type`` in the associated ``[ccpp-arg-table]`` section(s). See :numref:`Section %s <VariableTablesHostModel>` for more details regarding Host model metadata requirements.

#. ``name``:  This depends on the ``type``. For types ``ddt`` and ``module`` (for
   variable/type/kind definitions), ``name`` must match the name of the **single** associated
   ``[ccpp-arg-table]`` section. For type ``scheme``, the name must match the root names of the
   ``[ccpp-arg-table]`` sections for that scheme, without the suffixes
   ``_register``, ``_init``, ``_timestep_init``, ``_run``, ``_timestep_final``, or ``_final``.

#. ``dependencies``: type/kind/variable definitions and physics schemes often depend on code in other files
   (e.g. "use machine" --> depends on ``machine.F``). These dependencies must be provided as a comma-separated list.
   Relative path(s) to those file(s) must be specified here or using the ``relative_path`` entry described below.
   Dependency attributes are additive; multiple lines containing dependencies can be used. With the exception of
   specific files, such as ``machine.F``, which provides the `kind_phys` Fortran kind definition, shared dependencies
   between schemes are discouraged.

#. ``relative_path``: If specified, the relative path is added to every file listed in the ``dependencies``.

The information in this section table allows the CCPP to compile only the schemes and dependencies needed by the
selected CCPP suite(s).

An example for type and variable definitions from the file `ccpp-physics/physics/Radiation/RRTMG/radlw_param.meta <https://github.com/NCAR/ccpp-physics/blob/da75531/physics/Radiation/RRTMG/radlw_param.meta>`__ is shown in
:ref:`Listing 2.2 <table-properties-typedefs>`.

.. note::

   A single metadata file may require multiple instances of the ``[ccpp-table-properties]`` section. For example, if a scheme requires multiple derived data types, each should have its own ``[ccpp-table-properties]`` entry. Subsequent ``[ccpp-table-properties]`` sections should be preceded by a separating line of ``#`` characters, as shown in the examples on this page.

.. _table-properties-typedefs:
.. code-block:: fortran

   [ccpp-table-properties]
     name = topflw_type
     type = ddt
     dependencies =

   [ccpp-arg-table]
     name = topflw_type
     type = ddt

   ########################################################################
   [ccpp-table-properties]
     name = sfcflw_type
     type = ddt
     dependencies =

   [ccpp-arg-table]
     name = sfcflw_type
     type = ddt

   ########################################################################
   [ccpp-table-properties]
     name = proflw_type
     type = ddt
     dependencies =

   [ccpp-arg-table]
     name = proflw_type
     type = ddt

   ########################################################################
   [ccpp-table-properties]
     name = module_radlw_parameters
     type = module
     dependencies =

   [ccpp-arg-table]
     name = module_radlw_parameters
     type = module
   [topflw_type]
     standard_name = topflw_type
     long_name = definition of type topflw_type
     units = DDT
     dimensions = ()
     type = topflw_type
   [sfcflw_type]
     standard_name = sfcflw_type
     long_name = definition of type sfcflw_type
     units = DDT
     dimensions = ()
     type = sfcflw_type
   [proflw_type]
     standard_name = proflw_type
     long_name = definition of type proflw_type
     units = DDT
     dimensions = ()
     type = proflw_type

*Listing 2.2: Example of a CCPP-compliant metadata file showing the use of the [ccpp-table-properties] section and
how it relates to [ccpp-arg-table].*

An example metadata file for the CCPP scheme ``mp_thompson.meta`` (with many sections omitted as indicated by ``...``) is shown in :ref:`Listing 2.3 <table-properties-mp-thompson>`.

.. _table-properties-mp-thompson:
.. code-block:: fortran

   [ccpp-table-properties]
     name = mp_thompson
     type = scheme
     dependencies = machine.F,module_mp_radar.F90,module_mp_thompson.F90,module_mp_thompson_make_number_concentrations.F90

   ########################################################################
   [ccpp-arg-table]
     name = mp_thompson_init
     type = scheme
   [ncol]
     standard_name = horizontal_dimension
     long_name = horizontal dimension
     units = count
     dimensions = ()
     type = integer
     intent = in
   ...

   ########################################################################
   [ccpp-arg-table]
     name = mp_thompson_run
     type = scheme
   [ncol]
     standard_name = horizontal_dimension
     long_name = horizontal loop extent
     units = count
     dimensions = ()
     type = integer
     intent = in
   ...

   ########################################################################
   [ccpp-arg-table]
     name = mp_thompson_final
     type = scheme
   [errmsg]
     standard_name = ccpp_error_message
     long_name = error message for error handling in CCPP
     units = none
     dimensions = ()
     type = character
     kind = len=*
     intent = out
   ...

*Listing 2.3: Example metadata file for a CCPP-compliant physics scheme using a single*
``[ccpp-table-properties]`` *entry and how it defines dependencies for multiple* ``[ccpp-arg-table]`` *entries.
In this example the* timestep_init *and* timestep_final *phases are not used*.

ccpp-arg-table
--------------

For each CCPP compliant scheme, the ``ccpp-arg-table`` for a scheme, module or derived data type starts with this set of lines

.. code-block:: fortran

   [ccpp-arg-table]
    name = <name>
    type = <type>

* ``ccpp-arg-table`` indicates the start of a new metadata section for a given scheme.

* ``<name>`` is name of the corresponding subroutine/module.

* ``<type>`` can be ``scheme``, ``module``, or ``DDT``.

After the ``ccpp-arg-table``, there should be a metadata entry for every input and output argument to the scheme using the following format. Any attributes that are not listed as optional are required:

.. code-block:: fortran

   [varname]
    standard_name = <standard_name>
    long_name = <long_name>
    units = <units>
    dimensions = <dimensions>
    type = <type>
    kind = <kind>
    intent = <intent>
    optional = <True,False>
    top_at_one = <True,False>


* ``[varname]`` is the local name of the variable in the subroutine.

* ``standard_name`` is the standardized variable name for the given quantity, as specified in the Earth System Modeling Standard Names (https://github.com/ESCOMP/ESMStandardNames)

* ``long_name``  (*optional*) is a human-readable description of the variable contents.

* ``units`` denotes the physical units of the variable quantity. The units should be specified as space-separated SI abbreviations; e.g.

  * ``m2`` meters squared
  * ``mm s-1`` millimeters per second
  * ``W m-2`` Watts per meter squared
  * ``kg m-2 s-1`` kilograms per meter squared per second
  * For unitless quantities or other variables that do not fit into this categorization, see the `ESM Standard Names documentation <https://github.com/ESCOMP/ESMStandardNames/blob/main/StandardNamesRules.rst#units>`__ for more details


.. note:: The ``intent`` argument is only valid in ``scheme`` metadata tables, as it is not applicable to the other ``types``.

* ``dimensions`` indicates the dimensionality of the variable. The dimensions attribute should be empty parentheses for scalars, or indicate the start and end of each dimension of an array with an appropriate standard name; see the `ESM Standard Names documentation <https://github.com/ESCOMP/ESMStandardNames/blob/main/Metadata-standard-names.md#dimensions>`__. ``ccpp_constant_one`` is the assumed start for any dimension which only has a single value. Some examples are listed here:

.. code-block:: fortran

   dimensions = ()
   dimensions = (ccpp_constant_one:horizontal_dimension, vertical_level_dimension)
   dimensions = (horizontal_dimension,vertical_dimension)
   dimensions = (horizontal_dimension,vertical_dimension_of_ozone_forcing_data,number_of_coefficients_in_ozone_forcing_data)

* ``type`` indicates the variable type. Can be ``character``, ``integer``, ``real``, ``complex``, ``logical``, ``ddt``, or a custom type defined by the host. External (non-CCPP) types are also allowed and use the syntax: ``type = external:<module_name>:<type_name>``. For example, ``type = external:mpi_f08:mpi_comm``.

* ``kind`` (*optional*) indicates the variable kind, i.e. precision. The valid kinds are defined in the file `physics/hooks/machine.F <https://github.com/NCAR/ccpp-physics/blob/main/physics/hooks/machine.F>`__.

* ``intent`` indicates the argument intent for the given variable. Can be ``in``, ``out``, or ``inout``.

* ``optional`` (*optional*) indicates whether an argument is optional or not. If omitted, argument is assumed to be required.

* ``top_at_one`` (*optional*) indicates vertical orientation of variable. By default, this is set to False for all variables. This attribute can be set accordingly by the host and physics scheme(s) if there are different ordering conventions between them.

* Lines can be combined using ``|`` as a separator, e.g.,

.. code-block:: console

   type = real | kind = kind_phys


:ref:`Listing 2.4 <meta_template>` contains the template .meta file for an example CCPP-compliant scheme (``scheme_template.meta``)

.. _meta_template:
.. literalinclude:: ./_static/scheme_template.meta
   :language: fortran
   :lines: 10-40

*Listing 2.4: Fortran template for a metadata file accompanying a CCPP-compliant scheme.*

.. warning::
   The ``pointer`` and ``rank`` attributes are deprecated and no longer allowed in CCPP


.. _StandardNames:

Standard names
==============

Variables available for CCPP physics schemes are identified by their unique *standard name*. This
policy is in place to ensure that variables will always be unique and unambiguous when communicating
between different schemes and different host models. Schemes are free to use their own variable
names within their individual codes, but these variables must be assigned to a *standard name* within
the scheme's metadata table as described in :numref:`Section %s <IOVariableRules>`.

Standard names are listed and defined in a GitHub repository (https://github.com/ESCOMP/CCPPStandardNames),
along with rules for adding new standard names as needed. While an effort is made to comply with
existing *standard name* definitions of the Climate and Forecast (CF) conventions (http://cfconventions.org),
additional names are used in the CCPP to cover the wide range of use cases the CCPP intends to include.
Each hash of the CCPP Physics repository contains information in the top-level ``README.md`` file
indicating which version of the CCPPStandardNames repository corresponds to that version of CCPP code.

An up-to-date list of available standard names for a given host model can be found by running the CCPP *capgen* scripts (described in :numref:`Section %s <ccpp_datafile>`).

.. _IOVariableRules:

Input/Output Variable (argument) Rules
======================================

* A ``standard_name`` cannot be assigned to more than one local variable (``local_name``).
  The ``local_name`` of a variable can be chosen freely and does not have to match the
  ``local_name`` in the host model.

* All variable information (standard_name, units, dimensions) must match the specifications on
  the host model side, but sub-slices can be used/added in the host model. For example, when
  using the :term:`UFS Atmosphere` as the host model, tendencies are split in ``GFS_typedefs.meta``
  so they can be used in the necessary physics scheme:

  .. code-block:: fortran

     [dt3dt(:,:,1)]
       standard_name = cumulative_change_in_temperature_due_to_longwave_radiation
       long_name = cumulative change in temperature due to longwave radiation
       units = K
       dimensions = (horizontal_dimension,vertical_dimension)
       type = real
       kind = kind_phys
     [dt3dt(:,:,2)]
       standard_name = cumulative_change_in_temperature_due_to_shortwave_radiation
       long_name = cumulative change in temperature due to shortwave radiation
       units = K
       dimensions = (horizontal_dimension,vertical_dimension)
       type = real
       kind = kind_phys
     [dt3dt(:,:,3)]
       standard_name = cumulative_change_in_temperature_due_to_PBL
       long_name = cumulative change in temperature due to PBL
       units = K
       dimensions = (horizontal_dimension,vertical_dimension)
       type = real
       kind = kind_phys

  For performance reasons, slices of arrays should be contiguous in memory, which, in Fortran,
  implies that the dimension that is split is the rightmost (outermost) dimension as in the example above.

* The two mandatory variables that any scheme-related subroutine must accept as ``intent(out)`` arguments are
  ``errmsg`` and ``errflg`` (see also coding rules in :numref:`Section %s <CodingRules>`).

* At present, only two types of variable definitions are supported by the CCPP Framework:

   * Standard intrinsic Fortran variables are preferred (``character``, ``integer``, ``logical``, ``real``, ``complex``).
     For character variables, the length should be specified as ``*`` in order to allow the host model
     to specify the corresponding variable with a length of its own choice. All others can have a
     ``kind`` attribute of a ``kind`` type defined by the host model. For variables of type ``real``
     and ``complex`` without a ``kind`` attribute, the CCPP Framework will automatically assign the
     CCPP default floating point kind ``kind_phys`` to the variable's metadata.

   * Derived data types (DDTs). While the use of DDTs is discouraged, some use cases may
     justify their application (e.g. DDTs for chemistry that contain tracer arrays or information on
     whether tracers are advected). These DDTs must be defined by the scheme itself, not by the
     host model. It should be understood that use of DDTs within schemes
     forces their use in host models and potentially limits a scheme’s portability. Where possible,
     DDTs should be broken into components that could be usable for another scheme of the same type.

* It is preferable to have separate variables for physically-distinct quantities. For example,
  an array containing various cloud properties should be split into its individual
  physically-distinct components to facilitate generality. An exception to this rule is if
  there is a need to perform the same operation on an array of otherwise physically-distinct
  variables. For example, tracers that undergo vertical diffusion can be combined into one array
  where necessary. This tactic should be avoided wherever possible, and is not acceptable merely
  as a convenience.

* If a scheme is to make use of CCPP’s :term:`subcycling` capability, the current loop counter and the loop extent can be obtained from CCPP as ``intent(in)`` variables (see a :ref:`mandatory list of variables <MandatoryVariables>` that are provided by the CCPP Framework and/or the host model for this and other purposes).

* It is preferable to use assumed-size array declarations for input/output variables for CCPP schemes, i.e. instead of

  .. code-block:: fortran

     real(kind=kind_phys), dimension(is:ie,ks:ke), intent(inout) :: foo

  one should use

  .. code-block:: fortran

     real(kind=kind_phys), dimension(:,:), intent(inout) :: foo

  This allows the compiler to perform bounds checking and detect errors that otherwise may go unnoticed.

  .. warning:: Fortran assumes that the lower bound of assumed-size arrays is ``1``. If a scheme uses ``foo`` with lower bounds ``is`` and ``ks`` that are different from ``1``, then these must be specified explicitly:

  .. code-block:: fortran

     real(kind=kind_phys), dimension(is:,ks:), intent(inout) :: foo

* Optional arguments are allowed, and can be designated using the Fortran keyword ``optional`` in the variable declaration, and specifying ``optional = True`` in the variable attributes in the ``.meta`` file.


**Example from** `ccpp-physics/physics/SFC_Layer/MYNN/mynnsfc_wrapper.meta <https://github.com/NCAR/ccpp-physics/blob/da75531/physics/SFC_Layer/MYNN/mynnsfc_wrapper.meta>`__ **:**

  .. code-block:: fortran

     [ps]
       standard_name = surface_air_pressure
       long_name = surface pressure
       units = Pa
       dimensions = (horizontal_dimension)
       type = real
       kind = kind_phys
       intent = in 
     [PBLH]
       standard_name = atmosphere_boundary_layer_thickness
       long_name = PBL thickness
       units = m
       dimensions = (horizontal_dimension)
       type = real
       kind = kind_phys 
       intent = in
     [slmsk]
       standard_name = area_type
       long_name = landmask: sea/land/ice=0/1/2
       units = flag
       dimensions = (horizontal_dimension)
       type = real
       kind = kind_phys
       intent = in

     ...
     ...

     [qsfc_lnd_ruc]
       standard_name = water_vapor_mixing_ratio_at_surface_over_land
       long_name = water vapor mixing ratio at surface over land
       units = kg kg-1
       dimensions = (horizontal_dimension)
       type = real
       kind = kind_phys
       intent = in
       optional = True
     [qsfc_ice_ruc]
       standard_name = water_vapor_mixing_ratio_at_surface_over_ice
       long_name = water vapor mixing ratio at surface over ice
       units = kg kg-1
       dimensions = (horizontal_dimension)
       type = real
       kind = kind_phys
       intent = in
       optional = True

**Example from** `ccpp-physics/physics/SFC_Layer/MYNN/mynnsfc_wrapper.F90 <https://github.com/NCAR/ccpp-physics/blob/da75531/physics/SFC_Layer/MYNN/mynnsfc_wrapper.F90>`__ **:**

  .. code-block:: fortran

      real(kind_phys), dimension(:), intent(in)    ::       &
     &        dx, pblh, slmsk, ps
      real(kind_phys), dimension(:), intent(in),optional :: &
     &        qsfc_lnd_ruc, qsfc_ice_ruc

.. note:: Optional arguments **must** appear last (after all mandatory arguments) in the argument list

.. _CodingRules:

Coding Rules
============

* Code must comply to modern Fortran standards (Fortran 90 or newer).

* Use uppercase file suffixes (`.F`, `.F90`) to enable preprocessing by default.

* Labeled ``end`` statements should be used for modules, subroutines, functions, and type definitions;
  for example, ``module scheme_template → end module scheme_template``.

* Implicit variable declarations are not allowed. The ``implicit none`` statement is mandatory and
  is preferable at the module-level so that it applies to all the subroutines in the module.

* All ``intent(out)`` variables must be set inside the subroutine, including the mandatory
  variables ``errflg`` and ``errmsg``.

* Decomposition-dependent host model data inside the module cannot be permanent,
  i.e. variables that contain domain-dependent data cannot be kept using the ``save`` attribute.

* The use of ``goto`` statements is discouraged.

* ``common`` blocks are not allowed.

* Schemes are not allowed to abort/stop execution.

* Errors are handled by the host model using the two mandatory arguments ``errmsg`` and
  ``errflg``. In the event of an error, a meaningful error message should be assigned to ``errmsg``
  and ``errflg`` set to a value other than 0. For example:

.. code-block:: bash

   errmsg = ‘Logic error in scheme xyz: ...’
   errflg = 1
   return

* Schemes are not allowed to perform I/O operations except for reading lookup tables
  or other information needed to initialize the scheme, including stdout and stderr.
  Diagnostic messages are tolerated, but should be minimal.

* Line lengths of no more than 120 characters are suggested for better readability.

Additional coding rules are listed under the *Coding Standards* section of the NOAA NGGPS
Overarching System team document on Code, Data, and Documentation Management for NOAA Environmental
Modeling System (:term:`NEMS`) Modeling Applications and Suites (available at
https://docs.google.com/document/u/1/d/1bjnyJpJ7T3XeW3zCnhRLTL5a3m4_3XIAUeThUPWD9Tg/edit).

.. _UsingConstants:

Using Constants
===============
There are two principles that must be followed when using physical constants within CCPP-compliant physics schemes:

#. All schemes should use a single, consistent set of constants.
#. The host model must control (define and use) that single set, to provide consistency between a host model and the physics.

As long as a host application provides metadata describing its physical constants so that the CCPP framework can pass them to the physics schemes, these two principles are realized, and the CCPP physics schemes are model-agnostic.  Since CCPP-compliant hosts provide metadata about the available physical constants, they can be passed into schemes like any other data.

For simple schemes that consist of one or two files and only a few "helper" subroutines, passing in physical constants via the argument list and propagating those constants down to any subroutines that need them is the most direct approach.  The following example shows how the constant ``karman`` can be passed into a physics scheme:

.. code-block:: console

   subroutine my_physics_run(im,km,ux,vx,tx,karman)
     ...
   real(kind=kind_phys),intent(in)   ::  karman

Where the following has been added to the ``my_physics.meta`` file:

.. code-block:: console

   [karman]
     standard_name = von_karman_constant
     long_name = von karman constant
     units = none
     dimensions = ()
     type = real
     intent = in

This allows the von Karman constant to be defined by the host model and be passed in through the CCPP scheme subroutine interface.

For pre-existing complex schemes that contain many software layers and/or many "helper" subroutines that require physical constants, another method is accepted to ensure that the two principles are met while eliminating the need to modify many subroutine interfaces. This method passes the physical constants once through the argument list for the top-level ``_init`` subroutine for the scheme. This top-level ``_init`` subroutine also imports scheme-specific constants from a user-defined module.  For example, constants can be set in a module as:

.. code-block:: console

   module my_scheme_common
     use machine,     only : kind_phys
     implicit none
     real(kind=kind_phys)   ::  pi, omega1, omega2
   end module my_scheme_common

Within the ``_init`` subroutine body, the constants in the ``my_scheme_common`` module can be set to the ones that are passed in via the argument list, including any derived ones. For example:

.. code-block:: console

   module my_scheme
     use machine, only: kind_phys
     implicit none
     private
     public my_scheme_init, my_scheme_run, my_scheme_final
     logical :: is_initialized = .false.
   contains
     subroutine my_scheme_init (a, b, con_pi, con_omega)
       use my_scheme_common, only: pi, omega1, omega2
         ...
       pi = con_pi
       omega1 = con_omega
       omega2 = 2.*omega1
         ...
       is_initialized = .true.
     end subroutine my_scheme_init

     subroutine my_scheme_run (a, b)
       use my_scheme_common, only: pi, omega1, omega2
         ...
     end subroutine my_scheme_run

     subroutine my_scheme_final
         ...
       is_initialized = .false.
       pi = -999.
       omega1 = -999.
       omega2 = -999.
         ...
     end subroutine my_scheme_final
   end module my_scheme

After this point, physical constants can be imported from ``my_scheme_common`` wherever they are
needed. Although there may be some duplication in memory, constants within the scheme will be
guaranteed to be consistent with the rest of physics and will only be set/derived once during the
initialization phase. Of course, this will require that any constants in ``my_scheme_common`` that
are coming from the host model cannot use the Fortran ``parameter`` keyword. To guard against
inadvertently using constants in ``my_scheme_common`` without setting them from the host, they
should be initially set to some invalid value. The above example also demonstrates the use of
``is_initialized`` to guarantee idempotence of the ``_init`` routine. To clean up during the
final phase of the scheme, the ``is_initialized`` flag can be set back to false and the
constants can be set back to an invalid value.

In summary, there are two ways to pass constants to a physics scheme.  The first is to directly pass constants via the subroutine interface and continue passing them down to all subroutines as needed. The second is to have a user-specified scheme constants module within the scheme and to sync it once with the physical constants from the host model at initialization time. The approach to use is somewhat up to the developer.

.. note::

   Use of the *physcons* module (``ccpp-physics/physics/hooks/physcons.F90``) is **not recommended**, since it is specific to FV3 and will be removed in the future.

.. _ParallelProgramming:

Parallel Programming Rules
==========================

Most often, shared memory (OpenMP: Open Multi-Processing) and distributed memory (MPI: Message Passing Interface)
communication is done outside the physics, in which case the loops and arrays already
take into account the sizes of the threaded tasks through their input indices and array
dimensions.

`As of CCPP version 7 <https://github.com/NCAR/ccpp-framework/pull/523>`_, MPI is required as a prerequisite for building the CCPP framework in a host model.
While MPI directives are not required within physics schemes, developers are encouraged to make use of them where they may result in a significant speedup.
However, the following rules should be observed when including OpenMP or MPI communication in a physics scheme:

* MPI directives for Fortran code must be compatible with the Fortran 2008 standard, and must use the ``mpi_f08`` module
  rather than the legacy ``use mpi`` or ``INCLUDE 'mpif.h'``

* CCPP standards require that in every phase but the *run* phase, blocked data structures must be combined so that
  their entire contents are available to a given MPI task (i.e. the data structures can not be further subdivided, or
  "chunked", within those phases). The *run* phase may be called by multiple threads in parallel, so data structures
  may be divided into blocks for that phase.

* Shared-memory (OpenMP) parallelization inside a scheme is allowed with the restriction
  that the number of OpenMP threads to use is obtained from the host model as an ``intent(in)``
  argument in the argument list (:ref:`Listing 6.2 <MandatoryVariables>`).

* MPI communication is allowed in the *init*, *timestep_init*, *timestep_final*, and *final*,
  phases for the purpose of computing, reading or writing
  scheme-specific data that is independent of the host model’s data decomposition.

* If MPI is used, it is restricted to global communications: barrier, broadcast,
  gather, scatter, reduction. Point-to-point communication is not allowed. The
  MPI communicator must be passed to the physics scheme by the host model, the
  use of ``MPI_COMM_WORLD`` is not allowed (:ref:`see list of mandatory variables <MandatoryVariables>`).

* An example of a valid use of MPI is the initial read of a lookup table of aerosol
  properties by one or more MPI processes, and its subsequent broadcast to all processes.

* The implementation of reading and writing of data must be scalable to perform
  efficiently from one to thousands of tasks.

* Calls to MPI and OpenMP functions, and the import of the MPI and OpenMP libraries,
  must be guarded by C preprocessor directives as illustrated in the following listing.
  OpenMP pragmas can be inserted without C preprocessor guards, since they are ignored
  by the compiler if the OpenMP compiler flag is omitted.

.. code-block:: fortran

   #ifdef MPI
     use mpi_f08
   #endif
   #ifdef OPENMP
     use omp_lib
   #endif
   ...
   #ifdef MPI
     call MPI_BARRIER(mpicomm, ierr)
   #endif

   #ifdef OPENMP
     me = OMP_GET_THREAD_NUM()
   #else
     me = 0
   #endif

* If the error flag is set within a parallelized section of code, ensure that error flag is broadcast to all tasks/processes.

Memory allocation
-----------------

* **Schemes should not use dynamic memory allocation on the heap.**

* Schemes should not contain data that may clash when multiple non-interacting instances of the scheme are being used in one executable. This is because some host models may run multiple CCPP instances from the same executable.

* No variables should be allocated at the module level. Variables should either be allocated by the host model (for input and output variables) or within individual subroutines (for internal scheme variables).

.. include:: ScientificDocRules.inc

.. Bibliography should go at the end of the last chapter

.. bibliography:: references.bib
