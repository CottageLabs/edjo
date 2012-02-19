jQuery(document).ready(function() {
% for facet in c['config'].facets:
        $("#fh_${facet.field}").toggle(function(){ $("#fr_${facet.field}").show('fast');},function(){$("#fr_${facet.field}").hide('fast');});
% endfor
    });