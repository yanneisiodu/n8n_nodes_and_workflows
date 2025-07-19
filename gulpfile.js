const path = require('path');
const { task, src, dest, parallel } = require('gulp');

task('build:icons', copyIcons);
task('build:python', copyPythonScripts);
task('build:assets', parallel(copyIcons, copyPythonScripts));

function copyIcons() {
	const nodeSource = path.resolve('src', 'nodes', '**', '*.{png,svg}');
	const nodeDestination = path.resolve('dist', 'nodes');

	src(nodeSource).pipe(dest(nodeDestination));

	const credSource = path.resolve('src', 'credentials', '**', '*.{png,svg}');
	const credDestination = path.resolve('dist', 'credentials');

	return src(credSource).pipe(dest(credDestination));
}

function copyPythonScripts() {
	const pythonSource = path.resolve('src', 'nodes', '**', '*.py');
	const pythonDestination = path.resolve('dist', 'nodes');

	return src(pythonSource).pipe(dest(pythonDestination));
}
