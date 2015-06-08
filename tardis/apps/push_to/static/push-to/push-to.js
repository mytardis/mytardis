var pushToApp = angular.module('push-to', ['ngResource']);

pushToApp.controller('HostSelectCtrl', function($scope, $resource) {
    var CertSigningServices = $resource(cert_signing_services_url, {}, {get: {isArray: true}});
    var AccessibleHosts = $resource(accessible_hosts_url, {}, {get: {isArray: true}});

    $scope.loading = true;
    $scope.certHosts = [];

    $scope.accessibleHosts = [];
    var accessibleHosts = AccessibleHosts.get({}, function() {
        $scope.accessibleHosts = accessibleHosts;

        var certServices = CertSigningServices.get({}, function() {

            // Filter hosts allowed by SSH certificate signing, excluding hosts
            // that the user already has access to.
            for (var svcIdx = 0; svcIdx < certServices.length; svcIdx++) {
                var svc = certServices[svcIdx]
                for (var hostIdx = 0; hostIdx < svc.remote_hosts.length; hostIdx++) {
                    var h = svc.remote_hosts[hostIdx];
                    var found = false;
                    for (var i = 0; i < accessibleHosts.length; i++) {
                        if (accessibleHosts[i].id === h.id) {
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        $scope.certHosts.push(h);
                    }
                }
            }
        });
        $scope.loading = false;
    });
});