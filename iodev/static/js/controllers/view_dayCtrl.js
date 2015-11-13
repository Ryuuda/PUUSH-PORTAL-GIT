puushApp.controller('viewdayCtrl', function($scope, $log){

    $scope.status = {
        is1open: false,
        is2open: false,
        is3open: false,
        is4open: false,
        isFirstOpen: true,
        isFirstDisabled: false
    };

    $scope.toggled = function(open) {
        $log.log('Dropdown is now: ', open);
    };

    $scope.toggleDropdown = function($event) {
        $event.preventDefault();
        $event.stopPropagation();
        $scope.status.isopen = !$scope.status.isopen;
    };

    $scope.dynamicPopover = {
        templateUrl: 'myPopoverTemplate.html',
        title: 'More Options'
    };

});