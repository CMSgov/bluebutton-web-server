// Required Modules
const cleanCSS = require('gulp-clean-css');
const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));
const sourcemaps = require('gulp-sourcemaps');

// CSS Build Task
gulp.task('default', gulp.parallel(function (done) {
	gulp.src(['scss/static-main.scss', 'scss/sandbox-main.scss'],)
		.pipe(sourcemaps.init())
		.pipe(sass({
			includePaths: ['node_modules']
		}).on('error', sass.logError))
		.pipe(cleanCSS())
		.pipe(sourcemaps.write('.'))
		.pipe(gulp.dest('dist'));
	done();
}));

// CSS Watch Task
gulp.task('watch', gulp.series(function (done) {
	gulp.watch(['./scss/**/*.scss'], gulp.parallel('default'));
}));
