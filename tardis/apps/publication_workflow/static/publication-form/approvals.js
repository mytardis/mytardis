angular
.module('MyTardis')
.controller('PublicationApprovalsController', function ($scope, $log, $http) {

    var selectedPublicationId = null;
    var selectedAction = '';
    $scope.actionMessage = '';
    $scope.isSelected = function(publicationId, action) {
        if (selectedPublicationId !== null && angular.isDefined(action)) {
            return (selectedPublicationId === publicationId && selectedAction === action);
        } else if (selectedPublicationId !== null && angular.isUndefined(action)) {
            return (selectedPublicationId === publicationId);
        } else {
            return false;
        }
    };

    $scope.selectAction = function(publicationId, action) {
        selectedPublicationId = publicationId;
        selectedAction = action;
        $scope.actionMessage = '';
    };

    $scope.cancelAction = function() {
        selectedPublicationId = null;
        selectedAction = '';
        $scope.actionMessage = '';
    };

    $scope.isProcessing = false;

    $scope.submitAction = function() {
        $scope.isProcessing = true;
        $http.post('/apps/publication-workflow/approvals/',
                   {   'action':selectedAction,
                       'id':selectedPublicationId,
                       'message':$scope.actionMessage
                   }).success(function(response){
                       $scope.pendingPublications = response.data;
                       $scope.isProcessing = false;

                       selectedPublicationId = null;
                       selectedAction = '';
                       $scope.actionMessage = '';
                   }).error(function(response, status) {
                       $scope.isPending = false;
                       alert('Could not process this request (error code: '+status+')');
                   });

//        var idx = $scope.pendingPublications.indexOf(publication);
//        $scope.pendingPublications.splice(idx, 1);

//        selectedPublicationId = null;
//        selectedAction = '';
//        $scope.actionMessage = '';
    };

    $scope.refreshPendingPublications = function() {
        $http.post('/apps/publication-workflow/approvals/', {}).success(function (response) {
            $scope.pendingPublications = response.data;
        });
    };

    $scope.refreshPendingPublications();
});
