# Blue Button 2.0 CSS Resources

This is meant to be the central hub for all of the CSS resources used by the [Blue Button Static Site](https://bluebutton.cms.gov/), the [Blue Button Developer Sandbox](https://sandbox.bluebutton.cms.gov/), as well as any other necessary or future projects.

## Related Repositories

[Blue Button Static Site Repository](https://github.com/CMSgov/bluebutton-site-static)

[Blue Button Developer Sandbox Repository](https://github.com/CMSgov/bluebutton-web-server)

## MacOS/Linux Usage Instructions

First, clone the package to get started. Navigate to the your desired directory and run:

```bash
git clone git@github.com:CMSgov/bluebutton-css.git
```

Then:

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
