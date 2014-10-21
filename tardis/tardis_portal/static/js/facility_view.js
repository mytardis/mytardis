(function() {

  var app = angular.module('facility_view', []);

  // Capitalises the first letter (adapted from http://codepen.io/WinterJoey/pen/sfFaK)
  app.filter('capitalise', function() {
      return function(input, all) {
        return (!!input) ? input.replace(/([^\W_]+[^\s-]*) */g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();}) : '';
      }
  });

  app.controller('FacilityCtrl', function($scope, $http, $interval, $log, $filter) {

    // Whether to show the facility selector
    $scope.showFacilitySelector = function() {
      return ($scope.facilities.length > 1);
    }
    // Toggle the facility selector
    $scope.selectFacility = function(id, name) {
      $scope.selectedFacility = id;
      $scope.selectedFacilityName = name;
      $scope.fetchFacilityData();
    };
    // Check which facility is selected
    $scope.isFacilitySelected = function(id) {
      return $scope.selectedFacility === id;
    }

    // Toggle data view selector
    $scope.selectDataView = function(index) {
      $scope.selectedDataView = index;
    }
    // Check which data view is selected
    $scope.isDataViewSelected = function(index) {
      return $scope.selectedDataView === index;
    }

    // Toggle file list visibility
    $scope.toggleFileList = function(id) {
       if ($scope.visibleFileList === id) {
         delete $scope.visibleFileList;
       } else {
         $scope.visibleFileList = id;
       }
    }
    // Check if file list is visible
    $scope.isFileListVisible = function(id) {
      return $scope.visibleFileList === id;
    }
    $scope.unsetFileListVisibility = function() {
      delete $scope.visibleFileList;
    }

    // Reset filter form
    $scope.filterFormReset = function() {
       delete $scope.search_owner;
       delete $scope.search_experiment;
       delete $scope.search_instrument;
    }
    // Check if filters are active
    $scope.filtersActive = function() {
      if (typeof $scope.search_owner !== 'undefined' && $scope.search_owner.owner.name) {
        return true;
      } else if (typeof $scope.search_experiment !== 'undefined' && $scope.search_experiment.parent_experiment.title) {
        return true;
      } else if (typeof $scope.search_instrument !== 'undefined' && $scope.search_instrument.instrument.name) {
        return true;
      }
    }

    // Fetch the list of facilities available to the user and facilities data
    function initialiseFacilitiesData() {
      $http.get('/facility/fetch_facilities_list/').success(function(data) {
        $scope.facilities = data;
        if ($scope.facilities.length > 0) { // If the user is allowed to manage any facilities...
          $scope.selectedFacility = $scope.facilities[0].id;
          $scope.selectedFacilityName = $scope.facilities[0].name;
          $scope.fetchFacilityData();
        }
      });
    }

    // Fetch data for all facilities
    // callback is called after data is fetched
    $scope.fetchFacilityData = function(startIndex, endIndex, callback) {
      // Default range of values to fetch
      if (typeof startIndex === 'undefined') {
        startIndex = 0;
      }
      if (typeof endIndex === 'undefined') {
        endIndex = 100;
      }
      $http.get('/facility/fetch_data/'+$scope.selectedFacility+'/'+startIndex+'/'+endIndex+'/').success(function(data) {
        $scope.datasets = data;
        if ($scope.datasets.length > 0) {
          $scope.dataByUser = groupByUser($scope.datasets);
          $scope.dataByInstrument = groupByInstrument($scope.datasets);
        } else {
          $scope.dataByUser = [];
          $scope.dataByInstrument = [];
        }
      });
    }

    // Group facilities data by user
    function groupByUser(data) {
      // Sort by user ID
      data.sort(function(a,b) {a.owner.id - b.owner.id});
      
      var result = [];
      var tmp = {"owner":data[0].owner};
      tmp['datasets']=[];
      for (var i = 0; i < data.length; i++) {
        if (tmp.owner.id !== data[i].owner.id) {
          result.push(tmp);
          tmp = {"owner":data[i].owner};
          tmp['datasets'] = [];
        }
        var dataset = {};
        for (var key in data[i]) {
           if (key !== "owner") {
             dataset[key] = data[i][key];
           }
        }
        tmp['datasets'].push(dataset);
      }
      result.push(tmp);
      return result;
    }

    // Group facilities data by user
    function groupByInstrument(data) {
      // Sort by user ID
      data.sort(function(a,b) {a.instrument.id - b.instrument.id});

      var result = [];
      var tmp = {"instrument":data[0].instrument};
      tmp['datasets']=[];
      for (var i = 0; i < data.length; i++) {
        if (tmp.instrument.id !== data[i].instrument.id) {
          result.push(tmp);
          tmp = {"instrument":data[i].instrument};
          tmp['datasets'] = [];
        }
        var dataset = {};
        for (var key in data[i]) {
           if (key !== "instrument") {
             dataset[key] = data[i][key];
           }
        }
        tmp['datasets'].push(dataset);
      }
      result.push(tmp);
      return result;
    }

    // Refresh polling timer
    $interval(function() {
      if ($scope.refreshCountdown > 0 && $scope.refreshInterval > 0) {
        $scope.refreshCountdown--;
      } else if ($scope.refreshInterval > 0) {
        $scope.fetchFacilityData();
        $scope.refreshCountdown = $scope.refreshInterval;
      }
    }, 1000);

    // Set the update interval
    $scope.setRefreshInterval = function(interval) {
      $scope.refreshInterval = interval;
      $scope.refreshCountdown = interval;
    }

    // Format the countdown for the view (mm:ss)
    $scope.refreshCountdownFmt = function() {
      var minutes = Math.floor($scope.refreshCountdown / 60);
      var seconds = $scope.refreshCountdown - minutes * 60;
      if (minutes < 10) {
        var strMins = "0"+minutes;
      } else {
        var strMins = minutes;
      }
      if (seconds < 10) {
        var strSecs = "0"+seconds;
      } else {
        var strSecs = seconds;
      }
      return strMins + ":" + strSecs;
    }

    // Do initialisation
    initialiseFacilitiesData();
    $scope.facilities = [];
    $scope.selectedDataView = 1;
    $scope.refreshInterval = 0;
    $scope.refreshCountdown = 0;
  });

})();
