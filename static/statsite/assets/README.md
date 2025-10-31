# Blue Button Assets

## Custom SCSS

In addition to storing the `main.css` file and other critical assets, we are using this directory a temporary means of injecting custom scss/css into the template. To make changes to the custom scss files and have them exported, navigate to this directory and run one of the following commands:

To export the custom CSS:

`sass --watch scss/custom.scss:custom.css`

To minify and export the CSS (recommended):

`sass --watch scss/custom.scss:custom.css --style compressed`


*Windows Users:*

Sass is installed using Ruby. Ruby is installed by default on MacOS, but Windows may require you to install Ruby before you are able to install sass. To use the above commands, you may need a program like GitBash as well.
