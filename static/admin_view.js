(function () {
    'use strict';

    app

        .controller('AdminController', ['$scope', '$log', '$http', '$window',
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

                $scope.getClockTypes = function() {
                    var apiRoute = baseUrl + 'clock_types';
                    var _types = $http.get(apiRoute)
                        .then(function (response) {
                            $scope.clock_types = response.data;
                        },
                        function (error) {
                            $log.log(error);
                        });
                }; $scope.getClockTypes();

                $scope.setClockTypeChoice = function(entry, clock_type) {
                    entry.clock_type = clock_type;
                };

                $scope.setClockTypeChoiceNew = function(new_entry, clock_type) {
                    new_entry.clock_type = clock_type;
                };

                $scope.getUsers = function() {
                    var apiRoute = baseUrl + 'users';
                    var _users = $http.get(apiRoute)
                        .then(function (response) {
                            $scope.users = response.data;
                        },
                        function (error) {
                            $log.log(error);
                        });
                }; $scope.getUsers();

                $scope.getHoursWorked = function() {
                    if($scope.user_choice != 'Select User' && $scope.user_choice != null)
                    {
                        var user_id = $scope.user_choice;
                        var apiRoute = baseUrl + 'history/' + $scope.user_choice + '/get_hours';
                        var _hours = $http.post(apiRoute, {'startDate': $scope.startDate,
                                                            'endDate': $scope.endDate})
                        .then(function (response) {
                            var _hours = response.data.worked;
                            $scope.worked_hours = _hours == null ? '0.00 hours': _hours + ' hours';
                        },
                        function (error) {
                            $log.log(error);
                        });
                    }
                    else
                    {
                        $scope.worked_hours = '0.00 hours';
                    }
                }; $scope.getHoursWorked();

                $scope.save = function(entry) {
                    var apiRoute = baseUrl + 'entry/edit';
                    var _entry = $http.post(apiRoute, entry)
                        .then(function (response) {
                            $scope.getLogEntries($scope.user_choice);
                            //$scope.getHoursWorked();
                            entry.editing = false;
                            $scope.submit();
                            $scope.getHoursWorked();
                        },
                        function (error) {
                            $log.log(error);
                        });
                };

                $scope.edit = function(entry) {
                    entry.editing = true;
                };

                $scope.deleteEntry = function(entry) {
                    var apiRoute = baseUrl + 'entry/delete';
                    var _success = $http.post(apiRoute, {'entry_id': entry.entry_id})
                        .then(function (response) {
                            //$scope.getLogEntries($scope.user_choice);
                            $scope.log_entries.splice( $scope.log_entries.indexOf(entry), 1 );
                            $scope.getHoursWorked();
                        },
                        function (error) {
                            $log.log(error);
                        });
                };

                $scope.addEntry = function() {
                    var apiRoute = baseUrl + 'entry/add';
                    if (
                            $scope.new_entry.timestamp == null ||
                            $scope.new_entry.clock_type == null ||
                            $scope.user_choice == null ||
                            $scope.user_choice == 'Select User'
                        )
                    {
                    }
                    else
                    {
                        var _entry = $http.post(apiRoute,
                                        {'user': $scope.user_choice,
                                        'timestamp': $scope.new_entry.timestamp,
                                        'clock_type': $scope.new_entry.clock_type
                                })
                            .then(function (response) {
                                $scope.getLogEntries($scope.user_choice);
                                $scope.getHoursWorked();
                                $scope.submit();
                                $scope.getHoursWorked();
                            },
                            function (error) {
                                $log.log(error);
                            });
                        $scope.new_entry.timestamp = null;
                        $scope.new_entry.clock_type = null;
                    }
                };

                $scope.cancel = function(selected_entry) {
                    $scope.log_entries.forEach(function(entry) {
                        if (entry.entry_id === selected_entry.entry_id)
                        {
                            selected_entry.timestamp = entry.timestamp;
                            selected_entry.clock_type = entry.clock_type;
                            selected_entry.editing = false;
                        }
                    },
                    function (error) {
                        $log.log(error);
                    });
                };

                $scope.getLogEntries = function(id) {
                    var apiRoute = baseUrl + 'view/entries';
                    var _log_entries = $http.post(apiRoute, {'user':id,
                        'startDate': $scope.startDate,
                        'endDate': $scope.endDate})
                        .then(function (response) {
                            $scope.log_entries = response.data;
                        },
                        function (error) {
                            $log.log(error);
                        });
                };

                $scope.editLogEntry = function(selected_entry_id) {
                    var apiRoute = baseUrl + 'entry/edit';
                    var _result = $http.post(apiRoute, {'entry_id': selected_entry_id})
                        .then(function (response) {
                            $scope.log_entries.forEach(function(entry) {
                                if (entry.entry_id === selected_entry_id)
                                {
                                    entry.timestamp = response.data.timestamp;
                                    entry.clock_type = response.data.clock_type;
                                }
                            })
                        },
                        function (error) {
                            $log.log(error);
                        });
                };

                $scope.setUserChoice = function(id) {
                    $scope.user_choice = id != null ? id : 'Select User';
                    $scope.worked_hours = '0.00 hours';
                    $scope.log_entries = null;
                    $scope.endDate = null;
                    $scope.startDate = null;
                }; $scope.setUserChoice(null);

                $scope.submit = function() {
                    $scope.getHoursWorked();
                    $scope.getLogEntries($scope.user_choice);
                };

            }
        ]);
}());    
