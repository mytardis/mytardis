app.controller('publicationApprovals', function ($scope, $log, $http) {

    var selectedPublicationId = null;
    var selectedAction = '';
    $scope.actionMessage = '';
    $scope.isSelected = function(publication_id, action) {
        if (selectedPublicationId != null) {
            return (selectedPublicationId == publication_id && selectedAction == action);
        } else {
            return false;
        }
    }

    $scope.selectAction = function(publication_id, action) {
        selectedPublicationId = publication_id;
        selectedAction = action;
        $scope.actionMessage = '';
    }

    $scope.cancelAction = function() {
        selectedPublicationId = null;
        selectedAction = '';
        $scope.actionMessage = '';
    }

    $scope.submitAction = function(publication, message) {

        $http.post('/apps/publication-forms/approvals/',
            {   'action':selectedAction,
                'id':selectedPublicationId,
                'message':$scope.actionMessage
            }).success(function(data){
            $scope.pendingPublications = data;
        });

        var idx = $scope.pendingPublications.indexOf(publication);
        $scope.pendingPublications.splice(idx, 1);

        selectedPublicationId = null;
        selectedAction = '';
        $scope.actionMessage = '';
    }

    $scope.refreshPendingPublications = function() {
        $http.post('/apps/publication-forms/approvals/', {}).success(function (data) {
            $scope.pendingPublications = data;
        });
    }

    $scope.refreshPendingPublications();
});
