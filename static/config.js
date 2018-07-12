var app = angular.module('ClockApp', ['ui.bootstrap']);

app.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('//');
    $interpolateProvider.endSymbol('//');
});
