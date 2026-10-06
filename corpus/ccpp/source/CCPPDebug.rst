..  _CCPPDebug:

**************************************************
Debugging with CCPP
**************************************************

================================
Introduction
================================

In order to debug code efficiently with :term:`CCPP`, it is important to remember the conceptual differences between traditional, physics-driver based approaches and the ones with CCPP.

Traditional, physics-driver based approaches rely on hand-written physics drivers that connect the different physical :term:`parameterizations <parameterization>` together and often contain a large amount of "glue code" required between the parameterizations. As such, the physics drivers usually have access to all variables that are used by the physical parameterizations, while individual parameterizations only have access to the variables that are passed in. Debugging either happens on the level of the physics driver or inside physical parameterizations. In both cases, print statements are inserted in one or more places (e.g. in the driver before/after parameterizations to debug). In the CCPP, there are no hand-written physics drivers. Instead, the physical parameterizations are glued together by an :term:`SDF` that lists the :term:`primary physical parameterizations <primary scheme>` and so-called :term:`interstitial parameterizations <interstitial scheme>` or interstitial schemes (containing the glue code, broken up into logical units) in the order of execution.



=====================================
Two categories of debugging with CCPP
=====================================

* Debugging inside physical parameterizations
    Debugging the actual physical parameterizations is identical in CCPP and in physics-driver based models. The parameterizations have access to the same data and debug print statements can be added in exactly the same way.

* Debugging on a suite level
    Debugging on a :term:`suite` level, i.e. outside physical parameterizations, corresponds to debugging on the physics-driver level in traditional, physics-driver based models. In the CCPP, this can be achieved by using dedicated CCPP-compliant debugging schemes, which have access to all the data by requesting them via the metadata files. These schemes can then be called in any place in an SDF, except the ``fast_physics`` group, to produce the desired debugging output. The advantage of this approach is that debugging schemes can be moved from one place to another or duplicated by simply moving/copying a single line in the SDF before recompiling the code. The disadvantage is that different debugging schemes may be needed, depending on the :term:`host model` and their data structures. For example, the :term:`UFS` models use blocked data structures. The blocked data structures are commonly known as “GFS types”, are defined in ``GFS_typedefs.F90`` and exposed to the CCPP in ``GFS_typedefs.meta``. The rationale for this storage model is a better cache reuse by breaking up contiguous horizontal grid columns into N blocks with a predefined block size, and allocating each of the GFS types N times. For example, the 3-dimensional air temperature is stored as

    .. code-block:: console

        GFS_data(nb)%Statein%tgrs(1:IM,1:LM) with blocks nb=1,...,N

    Further, the UFS models run a subset of physics inside the dynamical core (“:term:`fast physics`”), for which the host model data is stored inside the dynamical core and cannot be shared with the traditional (“:term:`slow<slow physics>`”) physics. As such, different debugging schemes are required for the ``fast_physics`` group.


============================================
CCPP-compliant debugging schemes for the UFS
============================================
For the UFS models, dedicated debugging schemes have been created by the CCPP developers. These schemes can be found in `physics/Interstitials/UFS_SCM_NEPTUNE/GFS_debug.F90 <https://github.com/NCAR/ccpp-physics/blob/da75531/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_debug.F90>`__. Developers can use the schemes as-is or customize and add to them as needed. Also, several customization options are documented at the top of the file. These mainly deal with the amount/type of data/information output from arrays, and users can switch between them by turning on or off the corresponding preprocessor directives inside ``GFS_debug.F90``, followed by recompiling.

----------------------------------------------------------------
Descriptions of the CCPP-compliant debugging schemes for the UFS
----------------------------------------------------------------
* ``GFS_diagtoscreen``
    This scheme loops over all blocks for all GFS types that are persistent from one time step to the next (except ``GFS_control``) and prints data for almost all constituents. The call signature and rough outline for this scheme is:

      .. code-block:: console

            subroutine GFS_diagtoscreen_run (Model, Statein, Stateout, Sfcprop, Coupling,     &
                                         Grid, Tbd, Cldprop, Radtend, Diag, Interstitial, &
                                         nthreads, blkno, errmsg, errflg)
             ! Model / Control - only timestep information for now
            call print_var(mpirank, omprank, blkno, Grid%xlat_d, Grid%xlon_d, 'Model%kdt', Model%kdt)
            ! Sfcprop
            call print_var(mpirank, omprank, blkno, Grid%xlat_d, Grid%xlon_d, 'Sfcprop%slmsk', Sfcprop%slmsk)
            ...
            ! Radtend
            call print_var(mpirank, omprank, blkno, Grid%xlat_d, Grid%xlon_d, 'Radtend%sfcfsw%upfxc', Radtend%sfcfsw(:)%upfxc)
            ...
            !Tbd
            call print_var(mpirank, omprank, blkno, Grid%xlat_d, Grid%xlon_d, 'Tbd%icsdsw', Tbd%icsdsw)
            ...
            ! Diag
            call print_var(mpirank, omprank, blkno, Grid%xlat_d, Grid%xlon_d, 'Diag%srunoff', Diag%srunoff)
            ...
            ! Statein
            call print_var(mpirank, omprank, blkno, Grid%xlat_d, Grid%xlon_d, 'Statein%phii', Statein%phii)
            ! Stateout
            call print_var(mpirank, omprank, blkno, Grid%xlat_d, Grid%xlon_d, 'Stateout%gu0', Stateout%gu0)
            ...
            ! Coupling
            call print_var(mpirank, omprank, blkno, Grid%xlat_d, Grid%xlon_d, 'Coupling%nirbmdi', Coupling%nirbmdi)
            ...
            ! Grid
            call print_var(mpirank, omprank, blkno, Grid%xlat_d, Grid%xlon_d, 'Grid%xlon', Grid%xlon)
            ...
            end subroutine GFS_diagtoscreen_run


  .. _codeblockends:

            All output to ``stdout/stderr`` from this routine is prefixed with **'XXX: '** so that it can be easily removed from the log files using "grep -ve 'XXX: ' ..." if needed.



* ``GFS_interstitialtoscreen``
    This scheme is identical to ``GFS_diagtoscreen``, except that it prints data for all constituents of the ``GFS_interstitial`` derived data type only. As for ``GFS_diagtoscreen``, the amount of information printed to screen can be customized using preprocessor statements, and all output to ``stdout/stderr`` from this routine is prefixed with **'XXX: '** so that it can be easily removed from the log files using "grep -ve 'XXX: ' ..." if needed.



* ``GFS_abort``
    This scheme can be used to terminate a model run at some point in the call to the physics. It can be customized to meet the developer's requirements.

    .. code-block:: console

        subroutine GFS_abort_run (Model, blkno, errmsg, errflg)
            use machine,               only: kind_phys
            use GFS_typedefs,          only: GFS_control_type
            implicit none

            !--- interface variables
            type(GFS_control_type),   intent(in   ) :: Model
            integer,                  intent(in   ) :: blkno
            character(len=*),         intent(  out) :: errmsg
            integer,                  intent(  out) :: errflg
            ! Initialize CCPP error handling variables
            errmsg = ''
            errflg = 0
            if (Model%kdt==1 .and. blkno==size(Model%blksz)) then
                if (Model%me==Model%master) write(0,*) "GFS_abort_run: ABORTING MODEL"
                call sleep(10)
                stop
            end if
         end subroutine GFS_abort_run



* ``GFS_checkland``
    This routine is an example of a user-provided debugging scheme that is useful for solving issues with the fractional grid with the Rapid Update Cycle Land Surface Model (RUC LSM). All output to ``stdout/stderr`` from this routine is prefixed with **'YYY: '** (instead of ‘XXX:’), which can be easily removed from the log files using "grep -ve 'YYY: ' ..." if needed.

    .. code-block:: console

       subroutine GFS_checkland_run (me, master, blkno, im, kdt, iter, flag_iter, flag_guess, &
                                    flag_init, flag_restart, frac_grid, isot, ivegsrc, stype, vtype, slope,        &
                                    soiltyp, vegtype, slopetyp, dry, icy, wet, lake, ocean,                        &
                                    oceanfrac, landfrac, lakefrac, slmsk, islmsk, errmsg, errflg )
        ...
        do i=1,im
        !if (vegtype(i)==15) then
            write(0,'(a,2i5,1x,1x,l)') 'YYY: i, blk, flag_iter(i)  :', i, blkno, flag_iter(i)
            write(0,'(a,2i5,1x,1x,l)') 'YYY: i, blk, flag_guess(i) :', i, blkno, flag_guess(i)
            write(0,'(a,2i5,1x,e16.7)')'YYY: i, blk, stype(i)      :', i, blkno, stype(i)
            write(0,'(a,2i5,1x,e16.7)')'YYY: i, blk, vtype(i)      :', i, blkno, vtype(i)
            write(0,'(a,2i5,1x,e16.7)')'YYY: i, blk, slope(i)      :', i, blkno, slope(i)
            write(0,'(a,2i5,1x,i5)')   'YYY: i, blk, soiltyp(i)    :', i, blkno, soiltyp(i)
            write(0,'(a,2i5,1x,i5)')   'YYY: i, blk, vegtype(i)    :', i, blkno, vegtype(i)
            write(0,'(a,2i5,1x,i5)')   'YYY: i, blk, slopetyp(i)   :', i, blkno, slopetyp(i)
            write(0,'(a,2i5,1x,1x,l)') 'YYY: i, blk, dry(i)        :', i, blkno, dry(i)
            write(0,'(a,2i5,1x,1x,l)') 'YYY: i, blk, icy(i)        :', i, blkno, icy(i)
            write(0,'(a,2i5,1x,1x,l)') 'YYY: i, blk, wet(i)        :', i, blkno, wet(i)
            write(0,'(a,2i5,1x,1x,l)') 'YYY: i, blk, lake(i)       :', i, blkno, lake(i)
            write(0,'(a,2i5,1x,1x,l)') 'YYY: i, blk, ocean(i)      :', i, blkno, ocean(i)
            write(0,'(a,2i5,1x,e16.7)')'YYY: i, blk, oceanfrac(i)  :', i, blkno, oceanfrac(i)
            write(0,'(a,2i5,1x,e16.7)')'YYY: i, blk, landfrac(i)   :', i, blkno, landfrac(i)
            write(0,'(a,2i5,1x,e16.7)')'YYY: i, blk, lakefrac(i)   :', i, blkno, lakefrac(i)
            write(0,'(a,2i5,1x,e16.7)')'YYY: i, blk, slmsk(i)      :', i, blkno, slmsk(i)
            write(0,'(a,2i5,1x,i5)')   'YYY: i, blk, islmsk(i)     :', i, blkno, islmsk(i)
            !end if
        end do


-----------------------------------------------
How to use these debugging schemes for the UFS
-----------------------------------------------
Below is an example for an SDF that prints debugging output from the standard/persistent GFS types and the interstitial type in two places in the radiation group before aborting. Remember that the model loops through each group N block number of times (with potentially M different threads), hence the need to configure ``GFS_abort_run`` correctly (in the above example, it aborts for the last block, which is either the last loop or in the last group of the threaded loop).

    .. code-block:: console

      <?xml version="1.0" encoding="UTF-8"?>

      <suite name="FV3_GFS_v16" version="1">
      <!-- <init></init> -->
      <group name="fast_physics">
        ...
      </group>
      <group name="time_vary">
        ...
      </group>
      <group name="radiation">
        <subcycle loop="1">
          <scheme>GFS_suite_interstitial_rad_reset</scheme>
          <scheme>GFS_diagtoscreen</scheme>
          <scheme>GFS_interstitialtoscreen</scheme>
          <scheme>GFS_rrtmg_pre</scheme>
          <scheme>GFS_radiation_surface</scheme>
          <scheme>rad_sw_pre</scheme>
          <scheme>rrtmg_sw</scheme>
          <scheme>rrtmg_sw_post</scheme>
          <scheme>rrtmg_lw_pre</scheme>
          <scheme>rrtmg_lw</scheme>
          <scheme>rrtmg_lw_post</scheme>
          <scheme>GFS_rrtmg_post</scheme>
          <scheme>GFS_diagtoscreen</scheme>
          <scheme>GFS_interstitialtoscreen</scheme>
          <scheme>GFS_abort</scheme>
        </subcycle>
      </group>
      <group name="physics">
        ...
      </group>
      <group name="stochastics">
        ...
      </group>
      <!-- <finalize></finalize> -->
      </suite>

.. note::
   Users should be aware that the additional debugging output slows down model runs. It is recommended to reduce the forecast length (as often done for debugging purposes) or increase the walltime limit to debug efficiently. Other options to reduce the size of the output written to stdout/stderr is to use fewer MPI tasks, no OpenMP threading, or to set the blocksize such that each MPI task only has one block.

---------------------------------------------------------------------------
How to customize the debugging schemes and the output for arrays in the UFS
---------------------------------------------------------------------------

At the top of ``GFS_debug.F90``, there are customization options in the form of preprocessor directives (CPP ``#ifdef`` etc statements) and a brief documentation. Users not familiar with preprocessor directives are referred to the available documentation such as `Using fpp Preprocessor Directives <https://www.intel.com/content/www/us/en/develop/documentation/fortran-compiler-oneapi-dev-guide-and-reference/top/optimization-and-programming/fpp-preprocessing/using-fpp-preprocessor-directives.html>`_.

Currently three options exist: (1) full output of every element of each array if none of the #define preprocessor statements is used, (2) minimum, maximum, and mean value of arrays (default for GNU compiler), and (3) minimum, maximum, and 32-bit Adler checksum of arrays (default for Intel compiler). Note that Option (3), the Adler checksum calculation, cannot be used with gfortran (segmentation fault, bug in malloc?).

    .. code-block:: console

        !> \file GFS_debug.F90
        !!
        !! This is the place to switch between different debug outputs.
        !! - The default behavior for Intel (or any compiler other than GNU)
        !!   is to print minimum, maximum and 32-bit Adler checksum for arrays.
        !! - The default behavior for GNU is to minimum, maximum and
        !!   mean value of arrays, because calculating the checksum leads
        !!   to segmentation faults with gfortran (bug in malloc?).
        !! - If none of the #define preprocessor statements is used,
        !!   arrays are printed in full (this is often impractical).
        !! - All output to stdout/stderr from these routines are prefixed
        !!   with 'XXX: ' so that they can be easily removed from the log files
        !!   using "grep -ve 'XXX: ' ..." if needed.
        !! - Only one #define statement can be active at any time (per compiler)
        !!
        !! Available options for debug output:
        !!
        !!   #define PRINT_SUM: print minimum, maximum and mean value of arrays
        !!
        !!   #define PRINT_CHKSUM: minimum, maximum and 32-bit Adler checksum for arrays
        !!
        #ifdef __GFORTRAN__
        #define PRINT_SUM
        #else
        #define PRINT_CHKSUM
        #endif
