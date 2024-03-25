.. coding=utf-8
.. SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
.. SPDX-License-Identifier: MPL-2.0

=================
How to Contribute
=================

We'd love to accept your patches and contributions to this project. There are
just a few small guidelines you need to follow.

------------------------------------------
Filing bugs, change requests and questions
------------------------------------------

You can file bugs against, change requests for and questions about the project via github issues. Consult `GitHub Help <https://docs.github.com/en/free-pro-team@latest/github/managing-your-work-on-github/creating-an-issue>`__ for more
information on using github issues.

--------------------
Community Guidelines
--------------------
This project follows the following `Code of Conduct <./CODE_OF_CONDUCT.rst>`_.

-------------------
Source Code Headers
-------------------

Every file containing source code must include copyright and license
information. This includes any JS/CSS files that you might be serving out to
browsers. (This is to help well-intentioned people avoid accidental copying that
doesn't comply with the license.)

Mozilla header:

    SPDX-FileCopyrightText: 2023 Alliander N.V.

    SPDX-License-Identifier: MPL-2.0

-------------
Git branching
-------------

This project uses the `Gitflow Workflow <https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow>`_ and branching model. The `master` branch always contains the latest release, after a release is made new feature branches are branched of `develop`. When a feature is finished it is merged back into `develop`. At the end of a sprint `develop` is merged back into `master` or (optional) into a `release` branch first before it is merged into `master`.

![Gitflow](img/gitflow.svg)

------------
Code reviews
------------

All patches and contributions, including patches and contributions by project members, require review by one of the maintainers of the project. We
use GitHub pull requests for this purpose. Consult
`GitHub Help <https://help.github.com/articles/about-pull-requests/>`__ for more
information on using pull requests.

--------------------
Pull Request Process
--------------------

Contributions should be submitted as Github pull requests. See `Creating a pull request <https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request>`_ if you're unfamiliar with this concept.

The process for a code change and pull request you should follow:

1. Create a topic branch in your local repository, following the naming format:
   "feature-[description]". For more information see the `Git branching guideline <#git-branching>`_.
2. Make changes, compile, and test thoroughly. Ensure any install or build dependencies are removed before the end of the layer when doing a build. Code style should match existing style and conventions, and changes should be focused on the topic the pull request will be addressed. For more information see the `style guide <#source-code-headers>`_.
3. Push commits to your fork.
4. Create a Github pull request from your topic branch.
5. Pull requests will be reviewed by one of the maintainers who may discuss, offer constructive feedback, request changes, or approve
   the work. For more information see the `Code review guideline <#code-reviews>`_.
6. Upon receiving the sign-off of one of the maintainers you may merge your changes, or if you
    do not have permission to do that, you may request a maintainer to merge it for you.

-----------
Attribution
-----------

This Contributing.rst is adapted from Google
available at `https://github.com/google/new-project/blob/master/docs/contributing.rst <https://github.com/google/new-project/blob/master/docs/contributing.rst>`_
