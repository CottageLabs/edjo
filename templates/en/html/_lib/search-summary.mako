## -*- coding: utf-8 -*-

<div class="search_constraints">
## go through all of the search constraints
% for facet_name, values in c['results'].get_search_constraints().iteritems():
   <%
        facet = c['config'].get_facet(facet_name)
   %>
   ## if the search constraint is not an implicit facet, we display it
   % if facet is not None and facet.field not in c['implicit_facets']:
   
        ## if it is a ranged (range or date) facet, display the upper and lower bounds
        % if c['config'].is_range_facet(facet.field) or c['config'].is_date_facet(facet.field):
            <% 
                lower, upper = c['results'].get_range_values(facet.field)
            %>
            <div class="search_constraint">
                ${facet.display} : 
                % if upper != -1:
                    ${facet.get_value(lower)}
                    % if facet.display_upper(lower, upper):
                        - ${facet.get_value(upper)}
                    % endif
                % else:
                    ${facet.get_value(lower)}+
                % endif
                &nbsp;<a class="delete_url" href="${c['url_manager'].get_delete_url(facet.field)}">x</a>
            </div>
        
        ## if it is a field or query facet, display normally
        % else:
            % for value in values:
                <div class="search_constraint">
                    ${facet.display} : 
                    ${facet.get_value(value)}
                    &nbsp;<a class="delete_url" href="${c['url_manager'].get_delete_url(facet.field, value)}">x</a>
                </div>
            % endfor
        % endif
    
    % endif
% endfor
</div>


    