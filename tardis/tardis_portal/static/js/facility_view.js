/* eslint no-unused-vars: [2, {"vars": "local", "args": "none"}] */
// Capitalises the first letter (adapted from http://codepen.io/WinterJoey/pen/sfFaK)
angular
.module('MyTardis')
.filter('capitalise', function() {
    return function(input, all) {
        return (input) ? input.replace(/([^\W_]+[^\s-]*) */g, function(txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        }) : '';
    };
});

// Filter to produce nice file size formatting (adapted from https://gist.github.com/yrezgui/5653591)
angular
.module('MyTardis')
.filter('filesize', function() {
    var units = [
        'bytes',
        'KB',
        'MB',
        'GB',
        'TB',
        'PB'
    ];

    return function(bytes, precision) {
        if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) {
            return '?';
        }

        var unit = 0;

        while (bytes >= 1024) {
            bytes /= 1024;
            unit++;
        }

        return bytes.toFixed(+precision) + ' ' + units[unit];
    };
});


angular
.module('MyTardis')
.controller('FacilityController', function($resource, $interval, $log) {

    var vm = this; // view model

    var countRes = $resource('/facility/fetch_data/:facilityId/count/');
    var datasetDetailRes = $resource('/facility/fetch_datafiles/:dataset_id/',
        {}, {
            'get': {method: 'GET', isArray: true}
        });
    var facilityListRes = $resource('/facility/fetch_facilities_list/', {}, {
        'get': {method: 'GET', isArray: true}
    });
    var facilityDataRes = $resource('/facility/fetch_data/:facilityId/:startIndex/:endIndex/', {
        startIndex: 0,
        endIndex: 50
    }, {
        'get': {method: 'GET', isArray: true}
    });

    // Whether to show the "no data" alert
    vm.showDataUnvailableAlert = function() {
        if (vm.loading) {
            return false;
        } else if (angular.isDefined(vm.datasets)) {
            return vm.datasets.length === 0;
        } else {
            return true;
        }
    };

    // Whether to show the facility selector
    vm.showFacilitySelector = function() {
        return (vm.facilities.length > 1);
    };
    // Toggle the facility selector
    vm.selectFacility = function(id, name) {
        vm.selectedFacility = id;
        vm.selectedFacilityName = name;
        vm.currentFetchLimit = vm.defaultFetchLimit;
        vm.fetchFacilityData(0, vm.currentFetchLimit);
    };
    // Check which facility is selected
    vm.isFacilitySelected = function(id) {
        return vm.selectedFacility === id;
    };

    // Toggle data view selector
    vm.selectDataView = function(index) {
        vm.selectedDataView = index;
    };
    // Check which data view is selected
    vm.isDataViewSelected = function(index) {
        return vm.selectedDataView === index;
    };

    // Toggle file list visibility
    vm.toggleFileList = function(dataset) {
        if (vm.visibleFileList === dataset.id) {
            delete vm.visibleFileList;
        } else {
            vm.visibleFileList = dataset.id;
            datasetDetailRes.get({'dataset_id': dataset.id}).$promise.then(function(data) {
                dataset.datafiles = data;
            });
        }
    };
    // Check if file list is visible
    vm.isFileListVisible = function(id) {
        return vm.visibleFileList === id;
    };
    vm.unsetFileListVisibility = function() {
        delete vm.visibleFileList;
    };

    // Reset filter form
    vm.filterFormReset = function() {
        delete vm.search_owner;
        delete vm.search_experiment;
        delete vm.search_instrument;
    };
    // Check if filters are active
    vm.filtersActive = function() {
        if (angular.isDefined(vm.search_owner) && vm.search_owner.owner) {
            return true;
        } else if (angular.isDefined(vm.search_experiment) && vm.search_experiment.parent_experiment.title) {
            return true;
        } else if (angular.isDefined(vm.search_instrument) && vm.search_instrument.instrument.name) {
            return true;
        }
    };

    // Load more entries
    vm.loadMoreEntries = function(increment) {
        if (vm.currentFetchLimit >= vm.totalDatasets) {
            return;
        }
        if (vm.currentFetchLimit + increment > vm.totalDatasets) {
            vm.currentFetchLimit = vm.totalDatasets;
        } else {
            vm.currentFetchLimit += increment;
        }
        vm.fetchFacilityData(vm.datasets.length, vm.currentFetchLimit, true);
    };

    // Fetch the list of facilities available to the user and facilities data
    function initialiseFacilitiesData() {
        facilityListRes.get().$promise.then(function(data) {
                $log.debug("Facility list fetched successfully");
                vm.facilities = data;
                if (vm.facilities.length > 0) { // If the user is allowed to manage any facilities...
                    vm.selectedFacility = vm.facilities[0].id;
                    vm.selectedFacilityName = vm.facilities[0].name;
                    vm.fetchFacilityData(0, vm.defaultFetchLimit);
                }
            },
            function() {
                $log.error("Could not load facility list");
            });
    }

    // Fetch data for facility
    vm.fetchFacilityData = function(startIndex, endIndex, append) {

        delete vm.visibleFileList;
        vm.loading = true;

        countRes.get({'facilityId': vm.selectedFacility}).$promise.then(function(data) {
                $log.debug("Fetched total dataset count");
                vm.totalDatasets = data.facility_data_count;
                if (vm.currentFetchLimit > vm.totalDatasets) {
                    vm.currentFetchLimit = vm.totalDatasets;
                }
            },
            function() {
                $log.error("Could not fetch total dataset count");
            });

        facilityDataRes.get({
            'facilityId': vm.selectedFacility,
            'startIndex': startIndex,
            'endIndex': endIndex
        }).$promise.then(function(data) {
            $log.debug("Fetched datasets between indices " + startIndex + " and " + endIndex);
            if (append && vm.datasets) {
                vm.datasets = vm.datasets.concat(data.slice(0, data.length));
            } else {
                vm.datasets = data.slice(0, data.length);
            }
            if (vm.datasets.length > 0) {
                vm.dataByUser = groupByUser(vm.datasets);
                vm.dataByInstrument = groupByInstrument(vm.datasets);
            } else {
                vm.dataByUser = [];
                vm.dataByInstrument = [];
            }
        },
        function() {
            $log.error("Could not fetch datasets");
        })
        .finally(function() {
            vm.loading = false;
        });
    };

    // Group facilities data by user
    function groupByUser(data) {
        // Clone data, so we don't mess up the ordering
        // for the "Latest data" view.
        data = data.slice(0);
        // Sort by username, group name
        data.sort(function(a, b) {
            var aOwnerGroup = a.owner + ', ' + a.group;
            var bOwnerGroup = b.owner + ', ' + b.group;
            if (aOwnerGroup < bOwnerGroup) {
                return -1;
            } else if (aOwnerGroup > bOwnerGroup) {
                return 1;
            } else {
                return 0;
            }
        });

        var result = [];
        if (data[0].group) {
            data[0].ownerGroup = data[0].owner + ', ' + data[0].group;
        }
        else {
            data[0].ownerGroup = data[0].owner;
        }
        var tmp = {"ownerGroup": data[0].ownerGroup};
        tmp.datasets = [];
        for (var i = 0; i < data.length; i++) {
            data[i].ownerGroup = data[i].owner + ', ' + data[i].group;
            if (data[i].group) {
                data[i].ownerGroup = data[i].owner + ', ' + data[i].group;
            }
            else {
                data[i].ownerGroup = data[i].owner;
            }
            if (tmp.ownerGroup !== data[i].ownerGroup) {
                result.push(tmp);
                tmp = {"ownerGroup": data[i].ownerGroup};
                tmp.datasets = [];
            }
            var dataset = {};
            for (var key in data[i]) {
                if (key !== "ownerGroup") {
                    dataset[key] = data[i][key];
                }
            }
            tmp.datasets.push(dataset);
        }
        result.push(tmp);
        return result;
    }

    // Group facilities data by instrument
    function groupByInstrument(data) {
        // Clone data, so we don't mess up the ordering
        // for the "Latest data" view.
        data = data.slice(0);
        // Sort by instrument ID
        data.sort(function(a, b) {
            return a.instrument.id - b.instrument.id;
        });

        var result = [];
        var tmp = {"instrument": data[0].instrument};
        tmp.datasets = [];
        for (var i = 0; i < data.length; i++) {
            if (tmp.instrument.id !== data[i].instrument.id) {
                result.push(tmp);
                tmp = {"instrument": data[i].instrument};
                tmp.datasets = [];
            }
            var dataset = {};
            for (var key in data[i]) {
                if (key !== "instrument") {
                    dataset[key] = data[i][key];
                }
            }
            tmp.datasets.push(dataset);
        }
        result.push(tmp);
        return result;
    }

    // Refresh polling timer
    $interval(function() {
        if (vm.refreshCountdown > 0 && vm.refreshInterval > 0) {
            vm.refreshCountdown--;
        } else if (vm.refreshInterval > 0) {
            delete vm.visibleFileList;
            vm.fetchFacilityData(0, vm.currentFetchLimit);
            vm.refreshCountdown = vm.refreshInterval;
        }
    }, 1000);

    // Set the update interval
    vm.setRefreshInterval = function(interval) {
        vm.refreshInterval = interval;
        vm.refreshCountdown = interval;
    };

    // Format the countdown for the view (mm:ss)
    vm.refreshCountdownFmt = function() {
        var minutes = Math.floor(vm.refreshCountdown / 60);
        var seconds = vm.refreshCountdown - minutes * 60;
        var strMins, strSecs;
        if (minutes < 10) {
            strMins = "0" + minutes;
        } else {
            strMins = minutes;
        }
        if (seconds < 10) {
            strSecs = "0" + seconds;
        } else {
            strSecs = seconds;
        }
        return strMins + ":" + strSecs;
    };

    // Set default settings
    vm.defaultFetchLimit = 50;
    vm.currentFetchLimit = vm.defaultFetchLimit;
    vm.facilities = [];
    vm.selectedDataView = 1;
    vm.refreshInterval = 0;
    vm.refreshCountdown = 0;

    // Do initial data fetch
    initialiseFacilitiesData();

});
