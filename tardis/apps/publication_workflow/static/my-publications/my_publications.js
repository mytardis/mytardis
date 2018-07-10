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
    var scheduledPubsListRes = $resource('/apps/publication-workflow/scheduled_pubs_list/', {}, {
                    'get': {method: 'GET', isArray: true}
                        });
    var releasedPubsListRes = $resource('/apps/publication-workflow/released_pubs_list/', {}, {
                    'get': {method: 'GET', isArray: true}
                        });
    var retractedPubsListRes = $resource('/apps/publication-workflow/retracted_pubs_list/', {}, {
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

    /**
     * initializeScheduledPubsData
     *
     * Fetch the list of scheduled pubs available to the user
     */
    function initializeScheduledPubsData() {
        scheduledPubsListRes.get().$promise.then(function (data) {
                $log.debug("MyPublicationsController: Scheduled pubs list fetched successfully!");
                vm.scheduledPubs = data;
            },
            function () {
                $log.error("Could not load scheduled pubs list");
            });
    }

    /**
     * initializeReleasedPubsData
     *
     * Fetch the list of released pubs available to the user
     */
    function initializeReleasedPubsData() {
        releasedPubsListRes.get().$promise.then(function (data) {
                $log.debug("MyPublicationsController: Released pubs list fetched successfully!");
                vm.releasedPubs = data;
            },
            function () {
                $log.error("Could not load released pubs list");
            });
    }

    /**
     * initializeRetractedPubsData
     *
     * Fetch the list of retracted pubs available to the user
     */
    function initializeRetractedPubsData() {
        retractedPubsListRes.get().$promise.then(function (data) {
                $log.debug("MyPublicationsController: Retracted pubs list fetched successfully!");
                vm.retractedPubs = data;
            },
            function () {
                $log.error("Could not load retracted pubs list");
            });
    }

    // Do initial data fetch
    initializeDraftPubsData();
    initializeScheduledPubsData();
    initializeReleasedPubsData();
    initializeRetractedPubsData();

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

