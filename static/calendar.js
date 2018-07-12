(function () {
    'use strict';

    app

        .controller('HistoryController', ['$scope', '$log', '$http', '$window',
            function($scope, $log, $http, $window) {
                var baseUrl = '/timesheet/';

                $scope.alerts = [
                    //{ type: 'danger', msg: 'Oh snap! Change a few things up and try submitting again.' },
                    //{ type: 'success', msg: 'Well done! You successfully read this important alert message.' }
                ];

                $scope.addAlert = function(type, msg) {
                  $scope.alerts.push({'type': type, 'msg': msg});
                };

                $scope.closeAlert = function(index) {
                  $scope.alerts.splice(index, 1);
                };

                $scope.getHoursWorked = function() {
                    var apiRoute = baseUrl + 'history/get_hours';
                    var _hours = $http.post(apiRoute, {'startDate': $scope.startDate,
                                                        'endDate': $scope.endDate})
                    .then(function (response) {
                        var _hours = response.data.worked;
                        $scope.worked_hours = _hours == null ? '0.00 hours': _hours + ' hours';
                    },
                    function (error) {
                        $log.log(error);
                    });
                }; $scope.getHoursWorked();

                $scope.getLogEntries = function() {
                    var apiRoute = baseUrl + 'entries';
                    var _log_entries = $http.post(apiRoute,
                         {
                            'startDate': $scope.startDate,
                            'endDate': $scope.endDate
                         })
                        .then(function (response) {
                            $scope.log_entries = response.data;
                        },
                        function (error) {
                            $log.log(error);
                        });
                };

                $scope.submit = function() {
                    $scope.getLogEntries();
                    $scope.getHoursWorked();
                };
            }
        ]);
}());    


