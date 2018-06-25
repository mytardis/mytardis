/************************************************/
/* Gruntfile.js                                 */
/*                                              */
/* Usage:                                       */
/*                                              */
/* npm install                                  */
/* npm test                                     */
/*                                              */
/* OR                                           */
/*                                              */
/* npm install                                  */
/* ./node_modules/.bin/grunt test --verbose     */
/************************************************/

module.exports = function(grunt) {
    grunt.initConfig({
        qunit: {
            all: ['js_tests/tests.html']
        },
    });

    grunt.loadNpmTasks('grunt-contrib-qunit');
    grunt.registerTask('test', ['qunit']);
    grunt.registerTask('default', ['test']);
};
