..  _CodeManagement:

**************************************************
CCPP Code Management
**************************************************

================================
Organization of the Code
================================

This chapter describes the organization of the code, provides instruction on the GitHub workflow and the code review process, and outlines the release procedure. It is assumed that the reader is familiar with using basic GitHub features. A GitHub account is necessary if a user would like to make and contribute code changes to the :term:`CCPP`.

The repository and code organization differs for :term:`CCPP Framework` and :term:`CCPP Physics`.

--------------------------------------
CCPP Framework
--------------------------------------

The CCPP Framework code base can be found in the authoritative repository in the :term:`NCAR` GitHub organization (https://github.com/NCAR/ccpp-framework). This repository is public and can be viewed, downloaded, or cloned by users without needing a GitHub account.

Developers seeking to contribute code to the CCPP should create a GitHub account and set up a personal fork in order to introduce changes to the official code base via a Pull Request (PR) on GitHub (see `Creating Forks`_).

The following is the directory structure for the ``ccpp-framework`` repository:

.. code-block:: console

   ├── doc                    # Documentation for design/implementation and developers guide
   │   ├── DevelopersGuide
   │   ├── HelloWorld         # Toy model to use of the CCPP Framework
   │   └── img
   ├── capgen
   │   ├── generator          # CCPP code validator and generator
   │   ├── metadata           # CCPP metadata parsing
   │       └── parse_tools    # Parse utilities shared between parsing and validator
   │   ├── schema             # XML scheme for suite definition files
   │   ├── src                # CCPP framework source code
   ├── end-to-end-tests       # System testing framework for ccpp_capgen.py
   │       └── advection
   │       └── capgen
   │       └── chunked_data
   │       └── cmake
   │       └── constituents_dim
   │       └── ddthost
   │       └── instances
   │       └── instances_advection
   │       └── nested_suite
   │       └── opt_arg
   │       └── suite_allocate
   │       └── var_compat
   │       └── utils
   └── unit-tests

¹ see :numref:`Section %s <CCPP Stub Build>`

--------------------------------------
CCPP Physics
--------------------------------------

Because the CCPP Physics repository accepts contributions coming from multiple host models and applications, the code and repository organization is a bit more complex. The main "authoritative" code base for CCPP Physics can be found in the NCAR GitHub organization (https://github.com/NCAR/ccpp-physics). This repository is public and can be viewed, downloaded, or cloned by users without needing a GitHub account. However, in most cases code changes are not applied to this repository directly: Each :term:`host model` or application (aside from the :term:`SCM`) maintains its own Application Fork that accepts changes to CCPP Physics specifically in the context of that application. Code managers regularly sync changes from the Application Forks to the authoritative CCPP Physics repository in order to ensure a unified CCPP Physics code base. For more information about Application Forks, see `the GitHub Wiki Page <https://github.com/NCAR/ccpp-physics/wiki/Supporting-CCPP-for-various-host-models>`_.

Developers should create a personal fork from the appropriate Application Fork in order to introduce changes to the official code base via a Pull Request (PR) on GitHub (see `Creating Forks`_). Currently, the only Application Fork is for the UFS, so users should fork from there.

The following is the directory structure for the ``ccpp-physics`` repository (condensed version):

.. code-block:: console

   ├── physics                 # CCPP physics source code and metadata files
   │   ├── docs                # Scientific documentation (doxygen)
   │   │   ├── img             # Figures for doxygen
   │   │   └── pdftxt          # Text files for documentation
   └── tools                   # Tools used by CI system for basic checks (encoding ...)


=====================================================
GitHub Workflow (setting up development repositories)
=====================================================

The CCPP development practices make use of the GitHub forking workflow. For users not familiar with this concept, `this website <https://www.earthdatascience.org/workshops/intro-version-control-git/about-forks/>`_ provides some background information and a tutorial.

---------------
Creating Forks
---------------

The GitHub forking workflow relies on forks (personal copies) of the shared repositories on GitHub. A personal fork needs to be created only once, and only for repositories that users will contribute changes to. The following steps describe how to create a fork for CCPP development.

1.  Go to the repository you wish to fork, and make sure you are signed in to your GitHub account.

    * For CCPP Framework changes, this should be the authoritative repository (https://github.com/NCAR/ccpp-framework)
    * For CCPP Physics changes, this should be the Application Fork corresponding to your host model of interest
        * UFS Fork (https://github.com/ufs-community/ccpp-physics)

2. Select the "fork" button in the upper right corner.

      * If you have already created a fork, this will take you to your fork.
      * If you have not yet created a fork, this will create one for you.

.. note::
   If you already have a fork for a different CCPP Physics repository and so can not create a new one, contact the code managers via GitHub discussions (https://github.com/NCAR/ccpp-physics/discussions)

-----------------------------------
Checking out the Code
-----------------------------------
Instructions are provided here for the ccpp-physics repository assuming development intended for use in UFS Applications. The instructions for the ccpp-framework repository are analogous but should start from the main repository in the NCAR GitHub Organization (https://github.com/NCAR/ccpp-framework).

The process for checking out the CCPP is described in the following, assuming access via https (using a `personal access token <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens>`_) rather than ssh. If you are using an `ssh key <https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account>`_ instead, you should replace instances of ``https://github.com/`` with ``git@github.com:`` in repository URLs.

Start by checking out the UFS Application Fork:

.. code-block:: console

   git clone https://github.com/ufs-community/ccpp-physics
   cd ccpp-physics
   git remote rename origin upstream

In the above commands we have also renamed the "origin" repository to "upstream" within this clone. This will be required if you plan on making changes and contributing them back to your fork, but is otherwise unnecessary. This step prevents accidentally pushing changes to the main repository rather than your fork later on.

From here you can view the available branches in the ccpp-physics repository with the ``git branch`` command:

.. code-block:: console
   :emphasize-lines: 4-6

   git fetch --all
   git branch -a

   * ufs/dev
     remotes/upstream/HEAD -> upstream/ufs/dev
     remotes/upstream/ufs/dev

As you can see, you are placed on the ``ufs/dev`` branch by default; this is the most recent version of the development code in the ccpp-physics repository. In the ccpp-framework repository, the default branch is named ``main``. All new development should start from the default branch, but if you would like to view code from another branch this is simple with the ``git checkout`` command.

.. code-block:: console
   :emphasize-lines: 3-4

   git checkout release/public-v7

   branch 'release/public-v7' set up to track 'upstream/release/public-v7'.
   Switched to a new branch 'release/public-v7'

.. note::
   Never used git or GitHub before? Confused by what all this means or why we do it? Check out `this presentation from the UFS SRW Training workshop <https://dtcenter.org/sites/default/files/events/2021/18-code-management-making-contributions-kavulich.pdf>`_ for a "from basic principles" explanation!

After this command, git has checked out a local copy of the remote branch ``upstream/release/public-v7`` named ``release/public-v7``. To return to the ufs/dev branch, simply use ``git checkout ufs/dev``.

If you wish to make changes that you will eventually contribute back to the public code base, you should always create a new "feature" branch that will track those particular changes.

.. code-block:: console

   git checkout upstream/ufs/dev
   git checkout -b feature/my_new_local_development_branch

.. note::

   By checking out the remote ``upstream/ufs/dev`` branch directly, you will be left in a so-called '`detached HEAD <https://www.cloudbees.com/blog/git-detached-head>`_' state. This will prompt git to show you a scary-looking warning message, but it can be ignored so long as you follow it by the second command above to create a new branch.

You can now make changes to the code, and commit those changes locally using ``git commit`` in order to track



Once you are ready to contribute the code back to the main (``upstream``) ccpp-physics repository, you need to create a `pull request (PR) <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests>`_ (see `Creating a pull request`_). In order to do so, you first need to create your own fork of this repository (see `Creating Forks`_) and configure your fork as an additional remote destination, which we typically label as *origin*. For example:

.. code-block:: console

   git remote add origin https://github.com/YOUR_GITHUB_USER/ccpp-physics
   git fetch origin

Then, push your local branch to your fork:

.. code-block:: console

   git push origin my_local_development_branch

For each repository/submodule, you can check the configured remote destinations and all existing branches (remote and local):

.. code-block:: console

   git remote -v show
   git remote update
   git branch -a

As opposed to branches without modifications described in step 3, changes to the upstream repository can be brought into the local branch by pulling them down. For example (where a local branch is checked out):

.. code-block:: console

   cd ccpp-physics
   git remote update
   git pull upstream ufs/dev

.. _committing-changes:

==================================
Committing Changes to your Fork
==================================
Once you have your fork set up to begin code modifications, you should check that the cloned repositories upstream and origin are set correctly:

.. code-block:: console

   git remote -v

This should point to your fork as *origin* and the repository you cloned as *upstream*:

.. code-block:: console

   origin	      https://github.com/YOUR_GITHUB_USER/ccpp-physics (fetch)
   origin	      https://github.com/YOUR_GITHUB_USER/ccpp-physics (push)
   upstream   https://github.com/ufs-community/ccpp-physics (fetch)
   upstream   https://github.com/ufs-community/ccpp-physics (push)

Also check what branch you are working on:

.. code-block:: console

   git branch

This command will show what branch you have checked out on your fork:

.. code-block:: console

   * features/my_local_development_branch
     ufs/dev

After making modifications and testing, you can commit the changes to your fork.  First check what files have been modified:

.. code-block:: console

   git status

This git command will provide some guidance on what files need to be added and what files are “untracked”.  To add new files or stage modified files to be committed:

.. code-block:: console

   git add filename1 filename2

At this point it is helpful to have a description of your changes to these files documented somewhere, since when you commit the changes, you will be prompted for this information.  To commit these changes to your local repository and push them to the development branch on your fork:

.. code-block:: console

   git commit
   git push origin features/my_local_development_branch

When this is done, you can check the status again:

.. code-block:: console

   git status

This should show that your working copy is up to date with what is in the repository:

.. code-block:: console

   On branch features/my_local_development_branch
   Your branch is up to date with 'origin/features/my_local_development_branch'.
   nothing to commit, working tree clean

At this point you can continue development or create a PR as discussed in `Creating a Pull Request`_.

=========================================
Contributing Code, Code Review Process
=========================================
Once your development is mature, and the testing has been completed, you are ready to create a PR using GitHub to propose your changes for review.

-----------------------
Creating a Pull Request
-----------------------
Go to the github.com web interface, and navigate to your repository fork and branch. In most cases, this will be in the ccpp-physics repository, hence the following example:

 - Navigate to: https://github.com/<yourusername>/ccpp-physics
 - Use the drop-down menu on the left-side to select a branch to view your development branch
 - Use the button just right of the branch menu, to start a “New Pull Request”
 - Fill in a short title (one line)
 - Fill in a detailed description, including reporting on any testing you did
 - Click on “Create pull request”

If your development also requires changes in other repositories, you must open PRs in those repositories as well. In the PR message for each repository, please note the associated PRs submitted to other repositories.

Several people (aka CODEOWNERS) are automatically added to the list of reviewers on the right hand side. Once the PR has been approved, the change is merged to ufs/dev by one of the code owners. If there are pending conflicts, this means that the code is not up to date with the trunk. To resolve those, pull the target branch from upstream as described above, solve the conflicts and push the changes to the branch on your fork (this also updates the PR).

.. note::
   GitHub offers a "Draft pull request" feature that allows users to push their code to GitHub and create a draft PR. Draft PRs cannot be merged and do not automatically initiate notifications to the CODEOWNERS, but allow users to prepare the PR and flag it as “ready for review” once they feel comfortable with it. To open a draft rather than a ready-for-review PR, select the arrow next to the green "Create pull request" button, and select "Create draft pull request". Then continue the above steps as usual.
