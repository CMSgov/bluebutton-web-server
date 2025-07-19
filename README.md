Blue Button Web Server
=====================================================

[![Build Status](https://travis-ci.org/CMSgov/bluebutton-web-server.svg?branch=develop)](https://travis-ci.org/CMSGov/hhs_oauth_server)
[![Coverage Status](https://coveralls.io/repos/github/CMSgov/bluebutton-web-server/badge.svg?branch=develop)](https://coveralls.io/github/CMSgov/bluebutton-web-server?branch=develop)

This server serves as a data provider for sharing Medicare claims data with third parties.
The server connects to Medicare.gov for authentication, and uses OAuth2 to confirm permission
grants to external app developers. The data itself comes from a back end FHIR server
(https://github.com/CMSgov/bluebutton-data-server), which in turn pulls data from the CMS
Chronic Conditions Warehouse (https://www.ccwdata.org)

## About the Project

**This server serves as a data provider for sharing Medicare claims data with third parties. The server connects to Medicare.gov for authentication, and uses OAuth2 to confirm permission grants to external app developers.**

For more information on how to connect to the API implemented here, check out our developer documentation at https://cmsgov.github.io/bluebutton-developer-help/. Our most recent deployment is at https://sandbox.bluebutton.cms.gov, and you can also check out our Google Group at https://groups.google.com/forum/#!forum/developer-group-for-cms-blue-button-api for more details.

The information below outlines setting up the server for development or your own environment. For general information on deploying Django see https://docs.djangoproject.com/en/1.11/howto/deployment/.

NOTE: Internal software engineers or other interested parties should follow the documentation for running a Dockerized local development enviornment. For more information see https://github.com/CMSgov/bluebutton-web-server/blob/master/docker-compose/readme.md.

### Agency Mission

The Centers for Medicare & Medicaid Services (CMS) is working to enable Medicare beneficiaries to securely share their health data with applications of their choice through standards-based APIs.

## Core Team

A list of core team members responsible for the code and documentation in this repository can be found in [COMMUNITY.md](COMMUNITY.md).

## Repository Structure

<!--TREE START--><!--TREE END-->

**Main directories:**
- `apps/` - Django applications containing the core functionality
- `hhs_oauth_server/` - Main Django project settings and configuration
- `requirements/` - Python package requirements
- `docker-compose/` - Docker development environment setup
- `certstore/` - Certificate storage for x509 authentication (optional)

**Documentation Index:**
- `README.md` - This file, containing setup and usage instructions
- `CONTRIBUTING.md` - Guidelines for contributing to the project
- `COMMUNITY.md` - Community guidelines and code of conduct
- `SECURITY.md` - Security and vulnerability disclosure policies
- `LICENSE` - Apache 2.0 license

# Development and Software Delivery Lifecycle

The following guide is for members of the project team who have access to the repository as well as code contributors. The main difference between internal and external contributions is that external contributors will need to fork the project and will not be able to merge their own pull requests. For more information on contributing, see: [CONTRIBUTING.md](./CONTRIBUTING.md).

## Setup

These instructions provide a quick start for developers new to the project. Follow these steps on the command line.

```bash
# prepare your repository folder
git clone https://github.com/CMSGov/bluebutton-web-server.git
cd bluebutton-web-server

# create the virtualenv
python3 -m venv venv

# Install any prerequisites  (C headers, etc. This is OS specific)
# Ubuntu example
sudo apt-get install python3-dev libxml2-dev libxslt1-dev

# install the requirements
pip install --upgrade pip==9.0.1
pip install pip-tools
pip install -r requirements/requirements.txt

# prepare Django settings
cp hhs_oauth_server/settings/local_sample.txt hhs_oauth_server/settings/local.py
```

Note that most settings can be overridden by environment variables. See custom environment variables section below. Please ensure to create and use your own keys and secrets. See https://docs.djangoproject.com/en/1.11/topics/settings/ for more information. Continue the installation by issuing the following commands:

```bash
python manage.py migrate
python manage.py loaddata apps/accounts/fixtures/scopes_and_groups.json
python manage.py createsuperuser
python manage.py create_admin_groups
python manage.py create_blue_button_scopes
python manage.py create_test_user_and_application
```

The next step is optional: If your backend HAPI FHIR server is configured to require x509 certificates to access it then you need to obtain that keypair and place those files in certificate folder called `cerstore`.

```bash
mkdir ../certstore
(copy both x509 files, in PEM format, inside certstore)
```

If your backend FHIR server does not require certificate-based authorization then the previous step can be omitted.

Making calls to a back-end FHIR server requires that you set a series of variables before running tests or the server itself.

```bash
#Run the development server
python manage.py runserver
```

Note you can find the path to your Python3 binary by typing `which python3`.

## Local Development

### Docker Compose Setup

Instructions for running the development environment via `docker-compose` can be found [here](./docker-compose/readme.md)

### How to View the CSS/Styles Locally

To keep our CSS organized and consolidated across our applications, we use a dedicated [Blue Button CSS Repo](https://github.com/CMSgov/bluebutton-css).

In order to be able to see the styles locally for this project, you'll just need to clone the Blue Button CSS Repo at the root of this project.

From within `bluebutton-web-server`, run the following commands (Bash):

```bash
git clone git@github.com:CMSgov/bluebutton-css.git
```

*That should be all you need to get the styles working.* The instructions below will tell you how to work with or update the SCSS.

To get started making changes to the styles:

```bash
cd bluebutton-css
```

You'll need to make sure you have NodeJS installed. [Click here to find out more about NodeJS](https://nodejs.org/en/). Once you have NodeJs installed, run:

```bash
npm i
```

Finally, make sure you have Gulp 4.0 installed:

```bash
npm i gulp@4
```

*To export the CSS once, run:*

```bash
gulp
```

*To watch the SCSS files for changes, run:*

```bash
gulp watch
```

### Running Tests

Run the following:

```bash
python runtests.py
```

You can run individual applications tests or tests with in a specific area as well.

The following are a few examples (drilling down to a single test):

```bash
python runtests.py apps.dot_ext.tests
```

```bash
python runtests.py apps.dot_ext.tests.test_templates
```

```bash
python runtests.py apps.dot_ext.tests.test_templates.TestDOTTemplates.test_application_list_template_override
```

Multiple arguments can be provided too:

```bash
python runtests.py apps.dot_ext.tests apps.accounts.tests.test_login 
```

## Coding Style and Linters

Each application has its own linting and testing guidelines. Lint and code tests are run on each commit, so linters and tests should be run locally before committing.

## Branching Model

This project follows standard GitHub flow practices:

* Make changes in feature branches and merge to `main` frequently
* Pull-requests are reviewed before merging
* Tests should be written for changes introduced
* Each change should be deployable to production

## Contributing

Thank you for considering contributing to an Open Source project of the US Government! For more information about our contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Community

The Blue Button Web Server team is taking a community-first and open source approach to the product development of this tool. We believe government software should be made in the open and be built and licensed such that anyone can download the code, run it themselves without paying money to third parties or using proprietary software, and use it as they will.

We know that we can learn from a wide variety of communities, including those who will use or will be impacted by the tool, who are experts in technology, or who have experience with similar technologies deployed in other spaces. We are dedicated to creating forums for continuous conversation and feedback to help shape the design and development of the tool.

We also recognize capacity building as a key part of involving a diverse open source community. We are doing our best to use accessible language, provide technical and process documents, and offer support to community members with a wide variety of backgrounds and skillsets.

### Community Guidelines

Principles and guidelines for participating in our open source community are can be found in [COMMUNITY.md](COMMUNITY.md). Please read them before joining or starting a conversation in this repo or one of the channels listed below. All community members and participants are expected to adhere to the community guidelines and code of conduct when participating in community spaces including: code repositories, communication channels and venues, and events.

## Feedback

If you have ideas for how we can improve or add to our capacity building efforts and methods for welcoming people into our community, please let us know at **opensource@cms.hhs.gov**. If you would like to comment on the tool itself, please let us know by filing an **issue on our GitHub repository.**

## Using this Project

This project is free and open source software under the Apache2 license. You may add additional applications, authentication backends, and styles/themes are not subject to the Apache2 license.

In other words, you or your organization are not in any way prevented from build closed source applications on top of this tool. Applications that you create can be licensed in any way that suits you business or organizational needs. Any 3rd party applications are subject to the license in which they are distributed by their respective authors.

## Policies

### Open Source Policy

We adhere to the [CMS Open Source Policy](https://github.com/CMSGov/cms-open-source-policy). If you have any questions, just [shoot us an email](mailto:opensource@cms.hhs.gov).

### Security and Responsible Disclosure Policy

_Submit a vulnerability:_ Vulnerability reports can be submitted through [Bugcrowd](https://bugcrowd.com/cms-vdp). Reports may be submitted anonymously. If you share contact information, we will acknowledge receipt of your report within 3 business days.

For more information about our Security, Vulnerability, and Responsible Disclosure Policies, see [SECURITY.md](SECURITY.md).

### Software Bill of Materials (SBOM)

A Software Bill of Materials (SBOM) is a formal record containing the details and supply chain relationships of various components used in building software.

In the spirit of [Executive Order 14028 - Improving the Nation's Cyber Security](https://www.gsa.gov/technology/it-contract-vehicles-and-purchasing-programs/information-technology-category/it-security/executive-order-14028), a SBOM for this repository is provided here: https://github.com/CMSGov/bluebutton-web-server/network/dependencies.

For more information and resources about SBOMs, visit: https://www.cisa.gov/sbom.

## License

This project is free and open source software under the Apache 2 license. See LICENSE for more information.

## Public domain

This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/) as indicated in [LICENSE](LICENSE).

All contributions to this project will be released under the CC0 dedication. By submitting a pull request or issue, you are agreeing to comply with this waiver of copyright interest.