app.controller('publicationApprovals', function ($scope, $log, $http) {

    var selectedPublicationId = null;
    var selectedAction = '';
    $scope.actionMessage = '';
    $scope.isSelected = function(publication_id, action) {
        if (selectedPublicationId != null && typeof action !== 'undefined') {
            return (selectedPublicationId == publication_id && selectedAction == action);
        } else if (selectedPublicationId != null && typeof action === 'undefined') {
	    return (selectedPublicationId == publication_id);
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

    $scope.isProcessing = false;

    $scope.submitAction = function(publication, message) {
	$scope.isProcessing = true;
        $http.post('/apps/publication-workflow/approvals/',
		   {   'action':selectedAction,
                       'id':selectedPublicationId,
                       'message':$scope.actionMessage
		   }).success(function(data){
		       $scope.pendingPublications = data;
		       $scope.isProcessing = false;

		       selectedPublicationId = null;
		       selectedAction = '';
		       $scope.actionMessage = '';
		   }).error(function(data, status) {
		       $scope.isPending = false;
		       alert('Could not process this request (error code: '+status+')');
		   });

//        var idx = $scope.pendingPublications.indexOf(publication);
//        $scope.pendingPublications.splice(idx, 1);

//        selectedPublicationId = null;
//        selectedAction = '';
//        $scope.actionMessage = '';
    }

    $scope.refreshPendingPublications = function() {
        $http.post('/apps/publication-workflow/approvals/', {}).success(function (data) {
            $scope.pendingPublications = data;
        });
    }

    $scope.refreshPendingPublications();
});
