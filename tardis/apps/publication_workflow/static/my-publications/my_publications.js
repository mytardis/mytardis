/**
 * My Publications controller
 *
 */
angular
.module('MyTardis')
.controller('MyPublicationsController', function ($log, $resource, $timeout) {

    var vm = this;

    var draftPubsListRes = $resource('/apps/publication-workflow/draft_pubs_list/', {}, {
                    'get': {method: 'GET', isArray: true}
                        });

    /**
     * initializeDraftPubsData
     *
     * Fetch the list of draft pubs available to the user
     */
    function initializeDraftPubsData() {
        draftPubsListRes.get().$promise.then(function (data) {
                $log.debug("MyPublicationsController: Draft pubs list fetched successfully!");
                vm.draftPubs = data;
            },
            function () {
                $log.error("Could not load draft pubs list");
            });
    }

    // Do initial data fetch
    initializeDraftPubsData();

    vm.selected = [];
    vm.limitOptions = [5, 10, 15];

    vm.options = {
      rowSelection: true,
      multiSelect: true,
      autoSelect: true,
      decapitate: false,
      largeEditDialog: false,
      boundaryLinks: false,
      limitSelect: true,
      pageSelect: true
    };

    vm.query = {
      order: '-id',
      limit: 5,
      page: 1
    };

    vm.toggleLimitOptions = function () {
      vm.limitOptions = vm.limitOptions ? undefined : [5, 10, 15];
    };

    vm.loadStuff = function () {
      vm.promise = $timeout(function () {
        // loading
      }, 2000);
    }
 
    vm.logItem = function (item) {
      $log.debug(item.name + ' was selected');
    };

    vm.logOrder = function (order) {
      $log.debug('order: ' + order);
    };

    vm.logPagination = function (page, limit) {
      $log.debug('page: ' + page);
      $log.debug('limit: ' + limit);
    }
});

