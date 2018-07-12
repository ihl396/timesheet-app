(function () {
    'use strict';

    app

        .controller('UserController', ['$scope', '$log', '$http',
            function($scope, $log, $http) {
                $scope.getUser = function() {
                    var apiRoute = '/user';
                    var _user = $http.get(apiRoute);
                    _user.then(function (response) {
                        $scope.user = response.data;
                        $log.log($scope.user);
                    },
                    function (error) {
                        $log.log(error);
                    });
                }; $scope.getUser();
            }
        ]);
}());    
