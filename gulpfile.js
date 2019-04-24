// Required Modules
const cleanCSS 		= require('gulp-clean-css');
const gulp 				= require('gulp');
const minify 			= require('gulp-minify');
const pump 				= require('pump');
const rename			= require('gulp-rename');
const sass				= require('gulp-sass');
const sourcemaps	= require('gulp-sourcemaps');
const wait				= require('gulp-wait');

// CSS Task
/*
gulp.task('css', () => {
	pump([
		gulp.src(['scss/static-main.scss', 'scss/sandbox-main.scss']),
		sourcemaps.init(),
		sass().on('error', sass.logError),
		cleanCSS(),
		sourcemaps.write('.'),
		gulp.dest('dist')
	]);
});
*/

gulp.task('default', gulp.parallel(function(done) {
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

gulp.task('watch', gulp.series(function(done) {
	gulp.watch(['./scss/**/*.scss'], gulp.parallel('default'));
}));
