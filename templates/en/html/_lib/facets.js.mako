jQuery(document).ready(function() {
% for facet in c['config'].facets:
    <% field_name = facet.field.replace(".", "_") %>
        $("#fh_${field_name}").toggle(function(){ $("#fr_${field_name}").show('fast');},function(){$("#fr_${field_name}").hide('fast');});
% endfor
    });