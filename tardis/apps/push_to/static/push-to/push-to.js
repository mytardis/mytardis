var pushToApp = angular.module('push-to', ['ngResource', 'siyfion.sfTypeahead']);

pushToApp.controller('HostSelectCtrl', function ($scope, $resource) {
    var CertSigningServices = $resource(cert_signing_services_url, {}, {get: {isArray: true}});
    var AccessibleHosts = $resource(accessible_hosts_url, {}, {get: {isArray: true}});

    $scope.loading = true;
    $scope.certHosts = [];

    $scope.accessibleHosts = [];
    var accessibleHosts = AccessibleHosts.get({}, function () {
        $scope.accessibleHosts = accessibleHosts;

        var certServices = CertSigningServices.get({}, function () {

            // Filter hosts allowed by SSH certificate signing, excluding hosts
            // that the user already has access to.
            for (var svcIdx = 0; svcIdx < certServices.length; svcIdx++) {
                var svc = certServices[svcIdx];
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

pushToApp.controller('DestinationSelectorCtrl', function ($scope, $resource) {
    $scope.remote_destination_name = remote_destination_name;
    $scope.loading = true;
    $scope.destinationPath = null;

    var PathValidationService = $resource(remote_path_verify_url);

    var tokenizer = function (str) {
        return str.split("");
    };

    var currentQueryBase;
    var currentQuery;
    var validPaths = new Bloodhound({
        datumTokenizer: tokenizer,
        queryTokenizer: tokenizer,
        remote: {
            url: remote_path_verify_url + "?path=%QUERY",
            prepare: function (query, settings) {
                currentQuery = query;
                if (!query.endsWith("/")) {
                    var n = query.lastIndexOf('/');
                    query = query.substring(0, n !== -1 ? n : query.length) + "/";
                }
                currentQueryBase = query;
                settings.url = settings.url.replace("%QUERY", encodeURIComponent(query));
                return settings;
            },
            transform: function (data) {
                var transformedData = [];
                if(data.hasOwnProperty(currentQueryBase)) {
                    var queryResult = data[currentQueryBase];
                    var children = queryResult['valid_children'];
                    for (var i = 0; i < children.length; i++) {
                        var result = currentQueryBase + children[i];
                        if (result.startsWith(currentQuery)) {
                            transformedData.push(result)
                        }
                    }
                }
                return transformedData;
            },
            rateLimitWait: 100
        }
    });

    $scope.pathOptions = {
    highlight: true
    };

    $scope.pushUrl = "Fdsa";

    validPaths.initialize().then(function () {
        return PathValidationService.get({}).$promise.then(function (info) {
            $scope.destinationPath = info['default']['path'];
            $scope.defaultPath = $scope.destinationPath;
            $scope.loading = false;
        });
    });

    $scope.validPaths = {
        source: validPaths.ttAdapter()
    };
    
    $(document).ajaxStart(function() {
        $scope.ajaxRunning = true;
    })
    $(document).ajaxStop(function() {
        $scope.ajaxRunning = false;
    })
});