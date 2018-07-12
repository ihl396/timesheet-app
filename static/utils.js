app.filter('title', function() {
    return function(s) {
        return (angular.isString(s) && s.length > 0) ? s[0].toUpperCase() + s.substr(1).toLowerCase() : s;
    }
});

app.filter('check_clock_type', function() {
    return function(s) {
        return (angular.isString(s) && s.length > 0 && s != null) ? s : 'Select Clock';
    }
});
