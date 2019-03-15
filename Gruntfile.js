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
            all: ["js_tests/tests.html"],
            options: {
                puppeteer: {
                    // We need --disable-web-security to allow the JS unit
                    // tests to refer to paths not in the same origin (CORS)
                    // e.g. "../tardis/tardis_portal/static/js/main.js"
                    args: [
                        "--disable-web-security",
                        "--no-sandbox",
                        "--disable-setuid-sandbox"
                    ],
                }
            }
        }
    });

    grunt.loadNpmTasks("grunt-contrib-qunit");
    grunt.registerTask("test", ["qunit"]);
    grunt.registerTask("default", ["test"]);
};
