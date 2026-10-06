.. _ParamSpecOutput:

********************************
Parameterization-specific Output for UFS/SCM
********************************

========
Overview
========

When used with :term:`UFS` and the :term:`SCM`, the :term:`CCPP` offers the capability of outputting tendencies of temperature,
zonal wind, meridional wind, ozone, and specific humidity produced by the :term:`parameterizations <parameterization>` of selected
:term:`suites <suite>`. This capability is useful for understanding the behavior of the individual parameterizations in
terms of magnitude and spatial distribution of tendencies, which can help model developers debug, refine,
and tune their :term:`schemes <scheme>`.

The CCPP also enables outputting two-dimensional (2D) or three-dimensional (3D) arbitrary diagnostics
from the parameterizations. This capability is targeted to model developers who may benefit from analyzing
intermediate quantities computed in one or more parameterizations. One example of a desirable diagnostic is
tendencies from sub-processes within a parameterization, such as the tendencies from condensation,
evaporation, sublimation, etc. from a microphysics parameterization. The output is done using CCPP-provided
2D- and 3D arrays, and the developer can fill positions 1, 2, .., N of the array. Important aspects of the
implementation are that memory is only allocated for the necessary positions of the array and that all
diagnostics are output on physics model levels. An extension to enable output on radiation levels may be
considered in future implementations.

These capabilities of the SCM have been tested and are expected to work with the suites
``SCM_GFS_v16``, ``SCM_GFS_v16_RRTMGP``, ``SCM_GFS_v17_p8_ugwpv1``, ``SCM_WoFS_v0``, and ``SCM_HRRR_gf``.

==========
Tendencies
==========

This section describes the tendencies available, how to set the model to prepare them and how to output
them. It also contains a list of frequently-asked questions in :numref:`Section %s <AvailTendFAQ>`.

Available Tendencies
--------------------

The model can produce tendencies for temperature, wind, and all non-chemical tracers (see
:numref:`Table %s <avail_tend_variables>`) for several different schemes. Not all schemes produce all
tendencies.  For example, the orographic and convective gravity wave drag (GWD) schemes produce tendencies
of temperature and wind, but not of tracers. Similarly, only the planetary boundary layer (PBL), deep
and shallow convection, and microphysics schemes produce specific humidity tendencies.  Some PBL and
convection schemes will have tendencies for tracers, and others won't.

In addition to the tendencies from specific schemes, the output includes tendencies from all photochemical
processes, all physics processes, and all non-physics processes (last three rows of :numref:`Table %s
<avail_tend_processes>`). Examples of non-physical processes are dynamical core processes such as advection
and nudging toward climatological fields.

In the supported suites, there are two types of schemes that produce ozone tendencies: PBL and ozone
photochemistry. The total tendency produced by the ozone photochemistry scheme (NRL 2015 scheme) is
subdivided by subprocesses: production and loss (combined as a single subprocess), quantity of ozone present
in the column above a grid cell, influences from temperature, and influences from mixing ratio.  For more
information about the NRL 2015 ozone photochemistry scheme, consult the `CCPP Scientific Documentation
<https://dtcenter.ucar.edu/GMTB/v7.0.0/sci_doc/_g_f_s__o_z_p_h_y_s.html>`_.

There are numerous tendencies in CCPP, and you need to know which ones exist for your configuration to
enable them. The model will output a list of available tendencies for your configuration if you run with
diagnostic tendencies enabled. To avoid overusing memory, you should enable just one tendency, which is
available for all suites, the non-physics (ie. dynamics) tendency of temperature. Details of how to do this,
and how to use the information, is below.

Enabling Tendencies
-------------------

For performance reasons, the preparation of tendencies for output is off by default in the UFS and
can be turned on via a set of namelist options. Since the SCM is not operational and has a relatively
tiny memory footprint, these tendencies are turned on by default in the SCM.

There are three namelist variables associated with this capability: ``ldiag3d``, ``qdiag3d``, and
``dtend_select``. These are set in the ``&gfs_physics_nml`` portion of the namelist file ``input.nml``.

* ``ldiag3d`` enables tendencies for state variables (horizontal wind and temperature)
* ``qdiag3d`` enables tendencies for tracers; ``ldiag3d`` must also be enabled
* ``dtend_select`` enables only a subset of the tendencies turned on by ``ldiag3d`` and ``qdiag3d``

If ``dtend_select`` is not specified, the default is to select all tendencies enabled by the settings of
``ldiag3d`` and ``qdiag3d``.

Note that there is a fourth namelist variable, ``lssav``, associated with the output of
parameterization-specific information. The value of ``lssav`` is overwritten to true in the code, so the
value used in the namelist is irrelevant.

While the tendencies output by the SCM are instantaneous, the tendencies output by the UFS are averaged
over the number of hours specified by the user in variable ``fhzero`` in the ``&gfs_physics_nml`` portion of the
namelist file ``input.nml``. Variable ``fhzero`` must be an integer (it cannot be zero).

This example namelist selects all tendencies from microphysics processes, and all tendencies of
temperature. The naming convention for ``dtend_select`` is explained in the next section.

.. code:: fortran

   &gfs_physics_nml
     ldiag3d = .true. ! enable basic diagnostics
     qdiag3d = .true. ! also enable tracer diagnostics
     dtend_select = 'dtend*mp', 'dtend_temp_*' ! Asterisks (*) and question marks (?) have the same meaning as shell globs
     ! The default for dtend_select is '*' which selects everything
     ! ... other namelist parameters ...
   /

Tendency Names
--------------

Tendency variables follow the naming pattern below, which is used to enable calculation (``input.nml``) and output
of the variable:

.. code::

   dtend_variable_process

The ``dtend_`` string stands for "diagnostic tendency" and is used to avoid variable name clashes. Replace
``variable`` with the short name of the tracer or state variable (see :numref:`Table %s
<avail_tend_variables>`). Replace ``process`` with the short name of the process that is changing the
variable (see :numref:`Table %s <avail_tend_processes>`). For example, microphysics (``mp``) temperature
(``temp``) tendency is ``dtend_temp_mp``.

The next section will tell you how to determine which tendency variables are available for your model.

|

.. _avail_tend_variables:

.. table:: *Non-chemical tracer and state variables with tendencies. The second column is the* ``variable``
           *part of* ``dtend_variable_process``. *The Index column is the first index of* ``dtidx``. *Hence "X
           Wind" is at* ``dtend(:,:,dtidx(index_of_x_wind,:))``.


   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | **Variable**                                    | **Short**      | **Associated** | **dtidx**                | **Tendency Units**            |
   |                                                 | **Name**       | **Namelist**   | **Index**                |                               |
   |                                                 |                | **Variables**  |                          |                               |
   +=================================================+================+================+==========================+===============================+
   | Temperature                                     | ``temp``       | ``ldiag3d``    | ``index_of_temperature`` | K s\ :sup:`-1`                |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | X Wind                                          | ``u``          | ``ldiag3d``    | ``index_of_x_wind``      | m s\ :sup:`-2`                |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Y Wind                                          | ``v``          | ``ldiag3d``    | ``index_of_y_wind``      | m s\ :sup:`-2`                |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Water Vapor Specific Humidity                   | ``qv``         | ``qdiag3d``    | ``100+ntqv``             | kg kg\ :sup:`-1` s\ :sup:`-1` |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Ozone Concentration                             | ``o3``         | ``qdiag3d``    | ``100+ntoz``             | kg kg\ :sup:`-1` s\ :sup:`-1` |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Cloud Condensate or Liquid Water                | ``liq_wat``    | ``qdiag3d``    | ``100+ntcw``             | kg kg\ :sup:`-1` s\ :sup:`-1` |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Ice Water                                       | ``ice_wat``    | ``qdiag3d``    | ``100+ntiw``             | kg kg\ :sup:`-1` s\ :sup:`-1` |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Rain Water                                      | ``rainwat``    | ``qdiag3d``    | ``100+ntrw``             | kg kg\ :sup:`-1` s\ :sup:`-1` |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Snow Water                                      | ``snowwat``    | ``qdiag3d``    | ``100+ntsw``             | kg kg\ :sup:`-1` s\ :sup:`-1` |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Graupel                                         | ``graupel``    | ``qdiag3d``    | ``100+ntgl``             | kg kg\ :sup:`-1` s\ :sup:`-1` |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Cloud Amount                                    | ``cld_amt``    | ``qdiag3d``    | ``100+ntclamt``          | kg kg\ :sup:`-1` s\ :sup:`-1` |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Liquid Number Concentration                     | ``water_nc``   | ``qdiag3d``    | ``100+ntlnc``            | kg\ :sup:`-1` s\ :sup:`-1`    |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Ice Number Concentration                        | ``ice_nc``     | ``qdiag3d``    | ``100+ntinc``            | kg\ :sup:`-1` s\ :sup:`-1`    |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Rain Number Concentration                       | ``rain_nc``    | ``qdiag3d``    | ``100+ntrnc``            | kg\ :sup:`-1` s\ :sup:`-1`    |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Snow Number Concentration                       | ``snow_nc``    | ``qdiag3d``    | ``100+ntsnc``            | kg\ :sup:`-1` s\ :sup:`-1`    |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Graupel Number Concentration                    | ``graupel_nc`` | ``qdiag3d``    | ``100+ntgnc``            | kg\ :sup:`-1` s\ :sup:`-1`    |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Turbulent Kinetic Energy                        | ``sgs_tke``    | ``qdiag3d``    | ``100+ntke``             | J s\ :sup:`-1`                |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Mass Weighted Rime Factor                       | ``q_rimef``    | ``qdiag3d``    | ``100+nqrimef``          | kg kg\ :sup:`-1` s\ :sup:`-1` |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Number Concentration Of Water-Friendly Aerosols | ``liq_aero``   | ``qdiag3d``    | ``100+ntwa``             | kg\ :sup:`-1` s\ :sup:`-1`    |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Number Concentration Of Ice-Friendly Aerosols   | ``ice_aero``   | ``qdiag3d``    | ``100+ntia``             | kg\ :sup:`-1` s\ :sup:`-1`    |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Oxygen Ion Concentration                        | ``o_ion``      | ``qdiag3d``    | ``100+nto``              | kg kg\ :sup:`-1` s\ :sup:`-1` |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+
   | Oxygen Concentration                            | ``o2``         | ``qdiag3d``    | ``100+nto2``             | kg kg\ :sup:`-1` s\ :sup:`-1` |
   +-------------------------------------------------+----------------+----------------+--------------------------+-------------------------------+

|

.. _avail_tend_processes:

.. table:: *Processes that can change non-chemical tracer and state variables. The third column is the*
           ``process`` *part of* ``dtend_variable_process``. *The dtidx index is second index of dtidx, hence*
           *"Deep Convection" is at* ``dtend(:,:,dtidx(:,index_of_process_dcnv))``.

   +---------------------------------------+----------------+---------------+----------------------------------------+
   | **Process**                           | **diag_table** | **Short**     | **dtidx**                              |
   |                                       | **Module**     | **Name**      | **Index**                              |
   |                                       | **Name**       |               |                                        |
   +=======================================+================+===============+========================================+
   | Planetary Boundary Layer              | ``gfs_phys``   | ``pbl``       | ``index_of_process_pbl``               |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Deep Convection                       | ``gfs_phys``   | ``deepcnv``   | ``index_of_process_dcnv``              |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Shallow Convection                    | ``gfs_phys``   | ``shalcnv``   | ``index_of_process_scnv``              |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Microphysics                          | ``gfs_phys``   | ``mp``        | ``index_of_process_mp``                |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Convective Transport                  | ``gfs_phys``   | ``cnvtrans``  | ``index_of_process_conv_trans``        |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Long Wave Radiation                   | ``gfs_phys``   | ``lw``        | ``index_of_process_longwave``          |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Short Wave Radiation                  | ``gfs_phys``   | ``sw``        | ``index_of_process_shortwave``         |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Orographic Gravity Wave Drag          | ``gfs_phys``   | ``orogwd``    | ``index_of_process_orographic_gwd``    |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Rayleigh Damping                      | ``gfs_phys``   | ``rdamp``     | ``index_of_process_rayleigh_damping``  |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Convective Gravity Wave Drag          | ``gfs_phys``   | ``cnvgwd``    | ``index_of_process_nonorographic_gwd`` |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Production and Loss (Photochemical)   | ``gfs_phys``   | ``prodloss``  | ``index_of_process_prod_loss``         |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Ozone Mixing Ratio (Photochemical)    | ``gfs_phys``   | ``o3mix``     | ``index_of_process_ozmix``             |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Temperature-Induced (Photochemical)   | ``gfs_phys``   | ``temp``      | ``index_of_process_temp``              |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Overhead Ozone Column (Photochemical) | ``gfs_phys``   | ``o3column``  | ``index_of_process_overhead_ozone``    |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Sum of Photochemical Processes        | ``gfs_phys``   | ``photochem`` | ``index_of_process_photochem``         |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Sum of Physics Processes              | ``gfs_phys``   | ``phys``      | ``index_of_process_physics``           |
   | (Including Photochemical)             |                |               |                                        |
   +---------------------------------------+----------------+---------------+----------------------------------------+
   | Sum of Non-Physics Processes          | ``gfs_dyn``    | ``nophys``    | ``index_of_process_non_physics``       |
   +---------------------------------------+----------------+---------------+----------------------------------------+

Selecting Tendencies
--------------------

With the many suites and many combinations of schemes, it is hard to say which variable/process combinations
are available for your particular configuration. To find a list, enable diagnostics, but disable all
tracer/process combinations except one:

.. code:: fortran

   &gfs_physics_nml
     ldiag3d = .true. ! enable basic diagnostics
     qdiag3d = .true. ! also enable tracer diagnostics
     dtend_select = 'dtend_temp_nophys' ! All configurations have non-physics temperature tendencies
     ! ... other namelist parameters ...
   /

After recompiling and running the model, you will see lines like this in the model's standard output stream:

.. code:: console

   dtend selected: gfs_phys dtend_qv_mp = water vapor specific humidity tendency due to microphysics (kg kg-1 s-1)
   dtend selected: gfs_phys dtend_liq_wat_mp = cloud condensate (or liquid water) tendency due to microphysics (kg kg-1 s-1)
   dtend selected: gfs_phys dtend_rainwat_mp = rain water tendency due to microphysics (kg kg-1 s-1)
   dtend selected: gfs_phys dtend_ice_wat_mp = ice water tendency due to microphysics (kg kg-1 s-1)
   dtend selected: gfs_phys dtend_snowwat_mp = snow water tendency due to microphysics (kg kg-1 s-1)
   dtend selected: gfs_phys dtend_graupel_mp = graupel tendency due to microphysics (kg kg-1 s-1)
   dtend selected: gfs_phys dtend_cld_amt_mp = cloud amount integer tendency due to microphysics (kg kg-1 s-1)
   dtend selected: gfs_phys dtend_temp_phys = temperature tendency due to physics (K s-1)
   dtend selected: gfs_dyn dtend_temp_nophys = temperature tendency due to non-physics processes (K s-1)

There are three critical pieces of information in each line. Taking the third last line as an example,

1. ``dtend_cld_amt_mp`` -- this is the name of the variable in ``dtend_select``; for the UFS, it is also the name of the variable in the ``diag_table``
2. ``gfs_phys`` -- the ``diag_table`` module name (specific to the UFS, can be ignored for other models)
3. "cloud amount integer tendency due to microphysics" -- meaning of the variable

Note that the ``dtend_temp_nophys`` differs from the others in that it is in the ``gfs_dyn`` module
instead of ``gfs_phys`` because it sums non-physics processes. This is only relevant for the UFS.

Now that you know what variables are available, you can choose which to enable:

.. code:: fortran

   &gfs_physics_nml
     ldiag3d = .true. ! enable basic diagnostics
     qdiag3d = .true. ! also enable tracer diagnostics
     dtend_select = 'dtend*mp', 'dtend_temp_*' ! Asterisks (*) and question marks (?) have the same meaning as shell globs
     ! The default for dtend_select is '*' which selects everything
     ! ... other namelist parameters ...
   /

Note that any combined tendencies, such as the total temperature tendency from physics (``dtend_temp_phys``),
will only include other tendencies that were calculated. Hence, if you only calculate PBL and microphysics
tendencies then your "total temperature tendency" will actually just be the total of PBL and microphysics.

The third step is to enable output of variables, which will be discussed in the next section.


Outputting Tendencies
---------------------

UFS
^^^

After enabling tendency calculation (using ``ldiag3d``, ``qdiag3d``, and ``diag_select``), you must also
enable output of those tendencies using the ``diag_table``. Enter the new lines with the variables you want
output. Continuing our example from before, this will enable output of some microphysics tracer tendencies,
and the total tendencies of temperature:

.. code:: console

   "gfs_phys", "dtend_qv_mp",       "dtend_qv_mp",       "fv3_history", "all", .false., "none", 2
   "gfs_phys", "dtend_liq_wat_mp",  "dtend_liq_wat_mp",  "fv3_history", "all", .false., "none", 2
   "gfs_phys", "dtend_rainwat_mp",  "dtend_rainwat_mp",  "fv3_history", "all", .false., "none", 2
   "gfs_phys", "dtend_ice_wat_mp",  "dtend_ice_wat_mp",  "fv3_history", "all", .false., "none", 2
   "gfs_phys", "dtend_snowwat_mp",  "dtend_snowwat_mp",  "fv3_history", "all", .false., "none", 2
   "gfs_phys", "dtend_graupel_mp",  "dtend_graupel_mp",  "fv3_history", "all", .false., "none", 2
   "gfs_phys", "dtend_cld_amt_mp",  "dtend_cld_amt_mp",  "fv3_history", "all", .false., "none", 2
   "gfs_phys", "dtend_temp_phys",   "dtend_temp_phys",   "fv3_history", "all", .false., "none", 2
   "gfs_dyn",  "dtend_temp_nophys", "dtend_temp_nophys", "fv3_history", "all", .false., "none", 2

Note that all tendencies, except non-physics tendencies, are in the ``gfs_phys`` diagnostic module. The
non-physics tendencies are in the ``gfs_dyn`` module. This is reflected in the :numref:`Table %s <avail_tend_processes>`.

Note that some :term:`host models <host model>`, such as the UFS, have a limit of how many fields can be output in a run.
When outputting all tendencies, this limit may have to be increased. In the UFS, this limit is determined
by variable ``max_output_fields`` in namelist section ``&diag_manager_nml`` in file ``input.nml``.

Further documentation of the ``diag_table`` file can be found in the `UFS Weather Model User’s Guide <https://ufs-weather-model.readthedocs.io/en/release-public-v3/InputsOutputs.html#diag-table-file>`_.

When the model completes, the fv3_history file will contain these new variables.

SCM
^^^

The default behavior of the SCM is to output instantaneous values of all tendency variables, and
``dtend_select`` is not recognized. Tendencies are computed in file ``scm_output.F90`` in the
subroutines output_init and output_append. If the values of ``ldiag3d`` or ``qdiag3d`` are set to false, the
variables are still written to output but are given missing values.

.. _AvailTendFAQ:

FAQ
---

What is the meaning of error message ``max_output_fields`` was exceeded?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the limit to the number of output fields is exceeded, the job may fail with the following message:

.. code-block:: console

   FATAL from PE    24: diag_util_mod::init_output_field: max_output_fields =          300 exceeded.  Increase via diag_manager_nml

In this case, increase ``max_output_fields`` in ``input.nml``:

.. code-block:: console

   &diag_manager_nml
       prepend_date = .F.
       max_output_fields = 600

Why did I run out of memory when outputting tendencies?
-------------------------------------------------------

Trying to output all tendencies may use more memory than is available on your system.  Use ``dtend_select`` and choose your output
variables carefully!

Why did I get a runtime logic error when outputting tendencies?
---------------------------------------------------------------

Setting ``ldiag3d=F`` and ``qdiag3d=T`` will result in an error message:

.. code-block:: console

   Logic error in GFS_typedefs.F90: qdiag3d requires ldiag3d

If you want to output tracer tendencies, you must set both ``ldiag3d`` and ``qdiag3d`` to T. Then use
``diag_select`` to enable only the tendencies you want.  Make sure your ``diag_table`` matches your choice of tendencies specified through ``diag_select``.

Why are my tendencies zero, even though the model says they are supported for my configuration?
-----------------------------------------------------------------------------------------------

For total physics or total photochemistry tendencies, see the next question.

The tendencies will be zero if they are never calculated. Check that you enabled the tendencies with
appropriate settings of ``ldiag3d``, ``qdiag3d``, and ``diag_select``.

Another possibility is that the tendencies in question really are zero. The list of "available" tendencies
is set at the model level, where the exact details of schemes and suites are not known. This can lead to
some tendencies erroneously being listed as available. For example, some PBL schemes have ozone tendencies
and some don't, so some may have zero ozone tendencies. Also, some schemes don't have tendencies of state
variables or tracers. Instead, they modify different variables, which other schemes use to affect the state
variables and tracers. Unfortunately, not all of the 3D variables in CCPP have diagnostic tendencies.

Why are my total physics or total photochemistry tendencies zero?
-----------------------------------------------------------------

There are three likely reasons:

* You forgot to enable calculation of physics tendencies. Make sure ``ldiag3d`` and ``qdiag3d`` are T, and
  make sure ``diag_select`` selects physics tendencies.
* The suite did not enable the ``phys_tend`` scheme, which calculates the total physics and total
  photochemistry tendencies.
* You did not enable calculation of the individual tendencies, such as ozone. The ``phys_tend`` sums those
  to make the total tendencies.

====================================
Output of Auxiliary Arrays from CCPP
====================================

The output of diagnostics from one or more parameterizations involves changes to the
namelist and code changes in the parameterization(s) (to load the desirable information
onto the CCPP-provided arrays and to add them to the subroutine arguments) and in the
parameterization metadata descriptor file(s) (to provide metadata on the new subroutine
arguments). In the UFS, the namelist is used to control the temporal averaging period.
These code changes are intended to be used by scientists during the development process
and are not intended to be incorporated into the authoritative code. Therefore, developers
must remove any code related to these additional diagnostics before submitting a pull
request to the ``ccpp-physics`` repository.

The auxiliary diagnostics  from CCPP are output in arrays:

* aux2d  - auxiliary 2D array for outputting diagnostics
* aux3d  - auxiliary 3D array for outputting diagnostics

and dimensioned by:

* naux2d - number of 2D auxiliary arrays to output for diagnostics
* naux3d - number of 3D auxiliary arrays to output diagnostics

At runtime, these arrays will be written to the output files. Note that auxiliary
arrays can be output from more than one parameterization in a given run.

The UFS and SCM already contain code to declare and initialize the arrays:

* dimensions are declared and initialized in ``GFS_typedefs.F90``
* metadata for these arrays and dimensions are defined in ``GFS_typedefs.meta``
* arrays are populated in ``GFS_diagnostics.F90`` (UFS) or ``scm_output.F90`` (SCM)

The remainder of this section describes changes the developer needs to make in the
physics code and  in the host model control files to enable the capability. An
example (:numref:`Section %s  <CodeModExample>`) and FAQ (:numref:`Section %s <AuxArrayFAQ>`)
are also provided.

Enabling the auxiliary arrays capability
----------------------------------------

Physics-side changes
^^^^^^^^^^^^^^^^^^^^

In order to output auxiliary arrays, developers need to change at least the following
two files within the physics (see also example in :numref:`Section %s <CodeModExample>`):

* A CCPP entry point scheme (Fortran source code)
   * Add array(s) and its/their dimension(s) to the list of subroutine arguments
   * Declare array(s) with appropriate intent and dimension(s).  Note that array(s) do not
     need to be allocated by the developer.  This is done automatically in ``GFS_typedefs.F90``.
   * Populate array(s) with desirable diagnostic for output
* Associated CCPP metadata files for modified scheme(s)
   * Add entries for the array(s) and its/their dimension(s) and provide metadata

Host-side changes
^^^^^^^^^^^^^^^^^

UFS
"""

For the UFS,  developers have to change the following two files on the host side (also see
example provided in :numref:`Section %s <CodeModExample>`)

* Namelist file ``input.nml``
   * Specify how many 2D and 3D arrays will be output using variables ``naux2d`` and ``naux3d``
     in section ``&gfs_physics_nml``, respectively. The maximum allowed number of arrays to
     output is 20 2D and 20 3D arrays.
   * Specify whether the output should be for instantaneous or time-averaged quantities using
     variables ``aux2d_time_avg`` and ``aux_3d_time_avg``. These arrays are dimensioned ``naux2d``
     and ``naux3d``, respectively, and, if not specified in the namelist, take the default value F.
   * Specify the period of averaging for the arrays using variable ``fhzero`` (in hours).
* File ``diag_table``
   * Enable output of the arrays at runtime.
   * 2D and 3D arrays are written to the output files.

SCM
"""

Typically, in a 3D model, 2D arrays represent variables with two horizontal dimensions, e.g. x
and y, whereas 3D arrays represent variables with all three spatial dimensions, e.g. x, y, and z.
For the SCM, these arrays are implicitly 1D and 2D, respectively, where the “y” dimension is 1
and the “x” dimension represents the number of independent columns (typically also 1). For
continuity with the UFS Atmosphere, the naming convention 2D and 3D are retained, however.
With this understanding, the namelist files can be modified as in the UFS:

* Namelist file ``input.nml``
   * Specify how many 2D and 3D arrays will be output using variables ``naux2d`` and ``naux3d``
     in section ``&gfs_physics_nml``, respectively. The maximum allowed number of arrays to
     output is 20 2D and 20 3D arrays.
   * Unlike the UFS, only instantaneous values are output. Time-averaging can be done through
     post-processing the output. Therefore, the values of ``aux2d_time_avg`` and ``aux_3d_time_avg``
     should not be changed from their default false values. As such, the namelist variable ``fhzero``
     has no effect in the SCM.

.. _CodeModExample:

Recompiling and Examples
------------------------

The developer must recompile the code after making the source code changes to the CCPP scheme(s)
and associated metadata files. Changes in the namelist and diag table can be made after compilation.
At compile and runtime, the developer must pick suites that use the scheme from which output is desired.

An example for how to output auxiliary arrays is provided in the rest of this section. The lines that
start with “+” represent lines that were added by the developer to output the diagnostic arrays. In
this example, the developer modified the Grell-Freitas (GF) cumulus scheme to output two 2D arrays
and one 3D array. The 2D arrays are ``aux_2d (:,1)`` and ``aux_2d(:,2)``; the 3D array is ``aux_3d(:,:,1)``.
The 2D array ``aux2d(:,1)`` will be output with an averaging in time in the UFS, while the ``aux2d(:,2)``
and ``aux3d`` arrays will not be averaged.

In this example, the arrays are populated with bogus information just to demonstrate the capability.
In reality, a developer would populate the array with the actual quantity for which output is desirable.

.. code-block:: console

   diff --git a/physics/CONV/Grell_Freitas/cu_gf_driver.F90 b/physics/CONV/Grell_Freitas/cu_gf_driver.F90
   index df5a196b..a4fb7c1a 100644
   --- a/physics/CONV/Grell_Freitas/cu_gf_driver.F90
   +++ b/physics/CONV/Grell_Freitas/cu_gf_driver.F90
   @@ -68,7 +68,7 @@ contains
                   dfi_radar_max_intervals,ldiag3d,qci_conv,do_cap_suppress,        &
                   maxupmf,maxMF,do_mynnedmf,ichoice_in,ichoicem_in,ichoice_s_in,   &
                   spp_cu_deep,spp_wts_cu_deep,nchem,chem3d,fscav,wetdpc_deep,      &
   -               do_smoke_transport,kdt,errmsg,errflg)
   +               do_smoke_transport,kdt,errmsg,errflg,naux2d,naux3d,aux2d,aux3d)
    !-------------------------------------------------------------
          implicit none
          integer, parameter :: maxiens=1
   @@ -167,6 +167,11 @@ contains
       character(len=*), intent(out) :: errmsg
       integer,          intent(out) :: errflg
    
   +   integer, intent(in) :: naux2d,naux3d
   +   real(kind_phys), intent(inout) :: aux2d(:,:)
   +   real(kind_phys), intent(inout) :: aux3d(:,:,:)
   +
   +
    !  local variables
       integer, dimension(im) :: k22_shallow,kbcon_shallow,ktop_shallow
       real(kind=kind_phys), dimension (im)    :: rand_mom,rand_vmas
   @@ -261,6 +266,10 @@ contains
         errmsg = ''
         errflg = 0
    
   +     aux2d(:,1) = aux2d(:,1) + 1
   +     aux2d(:,2) = aux2d(:,2) + 2
   +     aux3d(:,:,1) = aux3d(:,:,1) + 3
   +
         ichoice   = ichoice_in
         ichoicem  = ichoicem_in
         ichoice_s = ichoice_s_in

The ``cu_gf_driver.meta`` file was modified accordingly:

.. code-block:: console

   diff --git a/physics/CONV/Grell_Freitas/cu_gf_driver.meta b/physics/CONV/Grell_Freitas/cu_gf_driver.meta
   index f76d0c30..1053325d 100644
   --- a/physics/CONV/Grell_Freitas/cu_gf_driver.meta
   +++ b/physics/CONV/Grell_Freitas/cu_gf_driver.meta
   @@ -687,3 +687,29 @@
      dimensions = ()
      type = integer
      intent = out
   +[naux2d]
   +  standard_name = number_of_2d_auxiliary_arrays
   +  long_name = number of 2d auxiliary arrays to output (for debugging)
   +  units = count
   +  dimensions = ()
   +  type = integer
   +[naux3d]
   +  standard_name = number_of_3d_auxiliary_arrays
   +  long_name = number of 3d auxiliary arrays to output (for debugging)
   +  units = count
   +  dimensions = ()
   +  type = integer
   +[aux2d]
   +  standard_name = auxiliary_2d_arrays
   +  long_name = auxiliary 2d arrays to output (for debugging)
   +  units = none
   +  dimensions = (horizontal_dimension,number_of_3d_auxiliary_arrays)
   +  type = real
   +  kind = kind_phys
   +[aux3d]
   +  standard_name = auxiliary_3d_arrays
   +  long_name = auxiliary 3d arrays to output (for debugging)
   +  units = none
   +  dimensions = (horizontal_dimension,vertical_layer_dimension,number_of_3d_auxiliary_arrays)
   +  type = real

The following lines were added to the ``&gfs_physics_nml`` section of the namelist file ``input.nml``:

.. code-block:: console

       naux2d         = 2
       naux3d         = 1
       aux2d_time_avg = .true., .false.

Recall that for the SCM, ``aux2d_time_avg`` should not be set to true in the namelist.

Lastly, the following lines were added to the ``diag_table`` for UFS:

.. code-block:: console

   # Auxiliary output
   "gfs_phys",    "aux2d_01",     "aux2d_01",      "fv3_history2d",  "all",  .false.,  "none",  2
   "gfs_phys",    "aux2d_02",     "aux2d_02",      "fv3_history2d",  "all",  .false.,  "none",  2
   "gfs_phys",    "aux3d_01",     "aux3d_01",      "fv3_history",    "all",  .false.,  "none",

.. _AuxArrayFAQ:

FAQ
^^^

How do I enable the output of diagnostic arrays from multiple parameterizations in a single run?
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Suppose you want to output two 2D arrays from schemeA and two 2D arrays from schemeB. You should
set the namelist to ``naux2d=4`` and ``naux3d=0``. In the code for schemeA, you should populate
``aux2d(:,1)`` and ``aux2d(:,2)``, while in the code for scheme B you should populate ``aux2d(:,3)``
and ``aux2d(:,4)``.
