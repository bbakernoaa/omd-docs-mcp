!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! CCPP-compliant physics scheme template
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!
! The general rules for CCPP-compliant physics schemes and metadata are described in file
! ccpp-doc/CCPPtechnical/source/CompliantPhysicsParams.rst.
!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    module scheme_template

      contains

!> \section arg_table_scheme_template_run Argument Table
!! \htmlinclude scheme_template_run.html
!!
      subroutine scheme_template_run (errmsg, errflg)

         implicit none

         !--- arguments
         ! add your arguments here
         character(len=*), intent(out)   :: errmsg
         integer,          intent(out)   :: errflg

         !--- local variables
         ! add your local variables here

         continue

         !--- initialize CCPP error handling variables
         errmsg = ''
         errflg = 0

         !--- initialize intent(out) variables
         ! initialize all intent(out) variables here

         !--- actual code
         ! add your code here

         ! in case of errors, set errflg to a value != 0,
         ! assign a meaningful message to errmsg and return

         return

      end subroutine scheme_template_run

    end module scheme_template
