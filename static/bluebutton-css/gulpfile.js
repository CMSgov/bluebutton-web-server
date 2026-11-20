// Required Modules
const cleanCSS = require('gulp-clean-css');
const gulp = require('gulp');
const replace = require('gulp-replace');
const sass = require('gulp-sass')(require('sass'));
const sourcemaps = require('gulp-sourcemaps');

// Strips JS vendor version numbers and copies to dist folder
// This is for Invicti scans
gulp.task('vendor-js', function () {
	return gulp.src([
		'node_modules/jquery/dist/jquery.min.js',
		'node_modules/bootstrap/dist/js/bootstrap.min.js',
	])
		.pipe(replace(/(\/\*! jQuery|Bootstrap) v\d+\.\d+\.\d+/, '$1'))
		.pipe(gulp.dest('dist'));
});

// CSS Build Task
gulp.task('default', gulp.parallel('vendor-js', function (done) {
	gulp.src(['scss/static-main.scss', 'scss/sandbox-main.scss'],)
		.pipe(sourcemaps.init())
		.pipe(sass({
			includePaths: ['node_modules']
		}).on('error', sass.logError))
		.pipe(cleanCSS())
		.pipe(sourcemaps.write('.'))
		.pipe(gulp.dest('dist'));
	gulp.src(['legacy-preserved.css'],)
		.pipe(sourcemaps.init())
		.pipe(cleanCSS())
		.pipe(sourcemaps.write('.'))
		.pipe(gulp.dest('dist'));
	done();
}));

// CSS Watch Task
gulp.task('watch', function () {
	gulp.watch(['./scss/**/*.scss'], gulp.series('default'));
});
