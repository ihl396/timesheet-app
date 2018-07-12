(function () {
    'use strict';

    app

        .service('TimesheetService', function ($http) {
            var urlGet = '';
            this.get = function(apiRoute) {
                return $http.get(apiRoute);
            };
            this.post = function(apiRoute, data) {
                return $http.post(apiRoute, data);
            };
        })
        .controller('ClockController', ['$scope', '$log', '$http', 'TimesheetService',
            function($scope, $log, $http, TimesheetService) {
                var baseUrl = '/timesheet/';
                $scope.getClock = function() {
                    var apiRoute = baseUrl + 'clock'
                    var _clock = TimesheetService.get(apiRoute);
                    _clock.then(function (response) {
                        $scope.clock_type = response.data;
                    },
                    function (error) {
                        $log.log(error);
                    });
                }; $scope.getClock();

                $scope.get_clock_data = function() {
                    var apiRoute = baseUrl + 'clock_entries';
                    var _clock = TimesheetService.get(apiRoute)
                    .then(function (response) {
                        $scope.clock_data = response.data;
                    },
                    function (error) {
                        $log.log(error);
                    });
                };
                $scope.get_clock_data();

                $scope.clickClock = function() {
                    var apiRoute = baseUrl + 'clock'
                    var _clock = TimesheetService.post(apiRoute, $scope.clock_type)
                    .then(function (response) {
                        $scope.getClock();
                        $scope.get_clock_data();
                    },
                    function (error) {
                        $log.log(error);
                    });
                };
            }
        ]);
}());    
