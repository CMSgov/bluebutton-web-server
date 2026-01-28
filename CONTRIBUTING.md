# How to Contribute

We're so thankful you're considering contributing to an [open source project of
the U.S. government](https://code.gov/)! If you're unsure about anything, just
ask -- or submit the issue or pull request anyway. The worst that can happen is
you'll be politely asked to change something. We appreciate all friendly
contributions.

We encourage you to read this project's CONTRIBUTING policy (you are here), its
[LICENSE](LICENSE.md), and its [README](README.md).

## Getting Started

If you're new to the project, look for issues labeled with `good-first-issue` or `help-wanted` to get started. These are typically easier problems that don't require deep knowledge of the codebase.

For more information on how to connect to the API implemented here, check out our [developer documentation](https://cmsgov.github.io/bluebutton-developer-help/). You can also check out our [Google Group](https://groups.google.com/forum/#!forum/developer-group-for-cms-blue-button-api) for community discussions.

### Team Specific Guidelines

The Blue Button Web Server project is maintained by the CMS team and welcomes contributions from external developers. Please review our [COMMUNITY.md](COMMUNITY.md) file for details on team structure, roles, and responsibilities. All contributors should be familiar with OAuth2, FHIR standards, and Django development practices.

### Building dependencies

These instructions provide a quick start for developers new to the project. You'll need Python 3, pip, and some system-level dependencies.

**System Requirements:**
- Python 3.x
- pip and pip-tools
- C headers and development tools

**Ubuntu/Debian example:**
```bash
sudo apt-get install python3-dev libxml2-dev libxslt1-dev
```

**Mac Homebrew example:**
```bash
brew install python libxml2 libxslt
```

**For other operating systems:** Install equivalent development packages for your platform.

### Building the Project

Follow these steps to set up your development environment:

```bash
# Clone the repository
git clone https://github.com/CMSGov/bluebutton-web-server.git
cd bluebutton-web-server

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install pip-tools
pip install -r requirements/requirements.txt
```

**Configure your environment:**
Copy the environment variables from .env.example to .env, editing what you need to for your local settings. 
Other environment variables used in the codebase are available in the docker-compose directory, in the different.env files. Please ensure to create and use your own keys and secrets.

**Initialize the database:**
```bash
python manage.py migrate
python manage.py loaddata apps/accounts/fixtures/groups.json
python manage.py createsuperuser
python manage.py create_admin_groups
python manage.py create_blue_button_scopes
python manage.py create_test_user_and_application
```

**Optional - Certificate setup:**
If your backend FHIR server requires x509 certificates:
```bash
mkdir ../certstore
# Copy both x509 files (in PEM format) to certstore directory
```

**Run the development server:**
```bash
python manage.py runserver
```

### Docker Compose Alternative

For a containerized development environment, see instructions in [docker-compose/readme.md](./docker-compose/readme.md).

### CSS/Styling Development

The majority of the styling this project uses is found within the static/ folder. This includes swagger, design-system, font-awesome, and a previously separate repository of scss called bluebutton-css.

To work with and build styles locally:

```bash
cd static/bluebutton-css
```

You'll need to make sure you have NodeJS installed. [Click here to find out more about NodeJS](https://nodejs.org/en/). Once you have NodeJs installed, run:

```bash
npm i
```

*To export the CSS once, run:*

```bash
npm run gulp
```

*To watch the SCSS files for changes, run:*

```bash
npm run gulp watch
```


### Workflow and Branching

We follow standard GitHub Flow practices:

1. **Fork the project** (external contributors) or create a branch (internal contributors)
2. **Check out the `master` branch**
3. **Create a feature branch** with a descriptive name
4. **Write code and tests** for your change
5. **From your branch, make a pull request** against `CMSGov/bluebutton-web-server/master`
6. **Work with repo maintainers** to get your change reviewed
7. **Wait for your change to be merged** into `master`
8. **Delete your feature branch** after successful merge

### Testing Conventions

**Running Tests:**
```bash
# Run all tests
python runtests.py

# Run specific application tests
python runtests.py apps.dot_ext.tests

# Run specific test modules
python runtests.py apps.dot_ext.tests.test_templates

# Run individual test methods
python runtests.py apps.dot_ext.tests.test_templates.TestDOTTemplates.test_application_list_template_override

# Run multiple test suites
python runtests.py apps.dot_ext.tests apps.accounts.tests.test_login
```

**Test Requirements:**
- Write tests for new functionality

### Coding Style and Linters

**Style Guidelines:**
- Write clear, self-documenting code with appropriate comments

**Linting:**
- Each application has its own linting guidelines

### Writing Issues

When creating an issue, please use this format:

```
module-name: One line summary of the issue (less than 72 characters)

### Expected behavior

As concisely as possible, describe the expected behavior.

### Actual behavior

As concisely as possible, describe the observed behavior.

### Steps to reproduce the behavior

1. List all relevant steps to reproduce the observed behavior
2. Include specific API calls, user actions, or configuration
3. Mention any relevant environment details

### Additional context

- Django version
- Python version
- Operating system
- Any relevant logs or error messages
```

See our `.github/ISSUE_TEMPLATE.md` for more examples.

### Writing Pull Requests

**Pull Request Guidelines:**
- File pull requests against the `master` branch
- Include a clear description of changes
- Reference any related issues
- Ensure all tests pass
- Include screenshots for UI changes

### Reviewing Pull Requests

**Review Process:**
The repository on GitHub is kept in sync with an internal repository at github.cms.gov. For the most part this process should be transparent to the project users, but it does have some implications for how pull requests are merged into the codebase.

When you submit a pull request on GitHub, it will be reviewed by the project community, and once the changes are approved, your commits will be brought into github.cms.gov's internal system for additional testing. Once the changes are merged internally, they will be pushed back to GitHub with the next sync.

## Documentation

We welcome improvements to the project documentation. This includes:

- API documentation updates
- Setup and configuration guides
- Developer tutorials
- Code comments and inline documentation

Please file an [issue](https://github.com/CMSGov/bluebutton-web-server/issues) for documentation improvements or submit a pull request with your changes.

**Documentation Resources:**
- Developer documentation: https://cmsgov.github.io/bluebutton-developer-help/
- Current deployment: https://sandbox.bluebutton.cms.gov
- Community discussions: https://groups.google.com/forum/#!forum/developer-group-for-cms-blue-button-api

## Policies

### Open Source Policy

We adhere to the [CMS Open Source Policy](https://github.com/CMSGov/cms-open-source-policy). If you have any questions, just [shoot us an email](mailto:opensource@cms.hhs.gov).

### Security and Responsible Disclosure Policy

_Submit a vulnerability:_ Vulnerability reports can be submitted through [Bugcrowd](https://bugcrowd.com/cms-vdp). Reports may be submitted anonymously. If you share contact information, we will acknowledge receipt of your report within 3 business days.

For more information about our Security, Vulnerability, and Responsible Disclosure Policies, see [SECURITY.md](SECURITY.md).

## Public domain

This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).

All contributions to this project will be released under the CC0 dedication. By submitting a pull request or issue, you are agreeing to comply with this waiver of copyright interest.