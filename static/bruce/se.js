jQuery(document).ready(function() {
    $("#one").toggle(function(){
        $(".onebox").hide('slow');
    },function(){
        $(".onebox").show('fast');
    });
});