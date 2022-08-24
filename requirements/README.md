## Vendoring Python requirements

This process allows us to download requirements for the application and store them in the `vendor` directory so that they may be installed during the build process without requiring access to the internet to do so.

NOTE: the files in the `vendor` directory are meant to be used with `linux_x86_64` platforms.

### Steps to edit/update application requirements:

1. Edit the `requirements/requirements.in` file
2. Edit the `requirements/requirements.dev.in` file
3. From the project root, run `make reqs-compile reqs-download`
4. Add and commit changes to `requirements/requirements.in`, `requirements/requirements.dev.in`, `requirements/requirements.txt`, `requirements/requirements.dev.txt` and any new or updated modules in the `vendor` directory
5. Later, to install the requirements from the `vendor` directory, run: `make reqs-install`
