/**
 * Tokens controller
 *
 */
/*eslint no-unused-vars: ["error", { "argsIgnorePattern": "^_" }]*/
angular
.module('publicationWorkflow')
.controller('PublicationTokensController', function (ngDialog, $scope, $log, $http, $resource) {
    var vm = this;
    vm.tokensListRes = $resource('/apps/publication-workflow/tokens_json/:publication_id/', {}, {
        'get': {method: 'GET', isArray: true}
    });
    if (angular.isDefined($scope.$parent.ngDialogData)) {
        vm.publicationId = $scope.$parent.ngDialogData.publicationId;
    }
    else {
        throw new Error("publicationId is undefined in PublicationTokensController");
    }

    vm.tokensListRes.get({'publication_id': vm.publicationId}).$promise.then(function (data) {
        vm.tokens = data;
    });

    // Create a token and open tokens dialog
    vm.createToken = function () {
        $http.post('/experiment/view/' + vm.publicationId + '/create_token/',
                   {'publication_id': vm.publicationId})
           .then(function (_response) {
               $log.debug("Created token successfully.");
                vm.tokensListRes.get({'publication_id': vm.publicationId}).$promise.then(function (data) {
                    vm.tokens = data;
                });
           },
           function(_response) {
               $log.debug("Failed to create token.");
           });
    };
    // Delete a token
    vm.deleteToken = function(token) {
        $http.post('/token/delete/' + token.id + '/', {})
           .then(function (_response) {
               $log.debug("Deleted token successfully.");
                vm.tokensListRes.get({'publication_id': vm.publicationId}).$promise.then(function (data) {
                    vm.tokens = data;
                });
           },
           function(_response) {
               $log.debug("Failed to delete token.");
           });
    };

});
