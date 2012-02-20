% for facet in c['config'].facets:

    ## we don't process implicit facets, they are immutable -->
    % if facet.field not in c['implicit_facets']:
        <% f = facet.field %>
        <% field_name = facet.field.replace(".", "_") %>
        ## a div to contain each facet -->
        <div class="facet">
        ## if the facet has values in the result set, display it and its facet values -->
        % if c['results'].has_values(facet.field):
        
            ## facet name, using its display form -->
            <div class="facet_heading">
                <a href="" id="fh_${field_name}">+&nbsp;${facet.display}</a>
            </div>
            
            ## first display the facet values which have already been selected -->
            <div id="selected_${field_name}" class="facet_value">
            
            ## if this is a ranged facet, display it as a range -->
            % if c['config'].is_range_facet(facet.field):
                ## ensure that we only display ranges which have been selected as part of 
                ##    the search (they are in the args) -->
                % if c['results'].in_args(facet.field):
                
                    ## get the range values -->
                    <% 
                        lower, upper = c['results'].get_range_values(facet.field)
                    %>
                    
                    ## if the end of the range is not -1, it has an upper boundary -->
                    % if upper != -1:
                        <em>
                        ${facet.get_value(lower)}
                        % if facet.display_upper(lower, upper):
                            - ${facet.get_value(upper)}
                        % endif
                        </em>
                    % else:
                        <em>${facet.get_value(lower)}+</em>
                    % endif
                    &nbsp;<a class="delete_url" href="${c['url_manager'].get_delete_url(facet.field)}">x</a><br/>
                    
                % endif
            ## if this is a date facet, display it as a date -->
            % elif c['config'].is_date_facet(facet.field):
            
                ## ensure that we only display ranges which have been selected as part of 
                ##    the search (they are in the args) -->
                % if c['results'].in_args(facet.field):
                
                    ## get the range values -->
                    <% 
                        lower, upper = c['results'].get_range_values(facet.field)
                    %>
                    
                    % if upper != -1:
                        <em>
                        ${facet.get_value(lower)}
                        % if facet.display_upper(lower, upper):
                            - ${facet.get_value(upper)}
                        % endif
                        </em>
                    % else:
                        <em>${facet.get_value(lower)}+</em>
                    % endif
                    &nbsp;<a class="delete_url" href="${c['url_manager'].get_delete_url(facet.field)}">x</a><br/>
                % endif 
                <% date_range = False %>
            ## if this is a field facet or a query facet, there can be more than
            ## one value, so we treat these slightly differently
            % else:
                % for value, count in c['results'].get_ordered_facets(facet.field):
                    % if c['results'].in_args(facet.field, value):
                        <div class="alert-message collapse-message search-constraint success">${facet.get_value(value)}
                            &nbsp;<a class="close unfloat" href="${c['url_manager'].get_delete_url(facet.field, value)}">x</a>
                        </div>
                    % endif
                % endfor
            % endif
            </div>
            
            
            
            
            ## next display the facet values which are available to be selected -->
            <div id="fr_${field_name}" style="display:none" class="facet_value">
            
            ## if this is a range facet, display the available ranges
            % if c['config'].is_range_facet(facet.field):
                <% range = True %>
                ## only display options if this facet is not already selected
                % if not c['results'].in_args(facet.field):
                    % for lower, upper, count in c['results'].get_ordered_facets(facet.field):
                        <div class="row">
                            <div class="span2">
                                <a href="${c['url_manager'].get_add_url(facet.field, lower, upper)}">
                                % if upper != -1:
                                    ${facet.get_value(lower)} - ${facet.get_value(upper)}
                                % else:
                                    ${facet.get_value(lower)}+ 
                                % endif
                                </a>
                            </div>
                            <div class="span1">
                                (${count})
                            </div>
                        </div>
                    % endfor
                % endif
                <% range = False %>
            ## if this is a date facet, display the available ranges
            % elif c['config'].is_date_facet(facet.field):
                <% date_range = True %>
                ## only display options if this facet is not already selected
                % if not c['results'].in_args(facet.field):
                    % for lower, upper, count in c['results'].get_ordered_facets(facet.field):
                        <div class="row">
                            <div class="span2">
                                <a href="${c['url_manager'].get_add_date_url(facet.field, lower, upper)}">
                                % if upper != -1:
                                    ${facet.get_value(lower)}
                                    % if facet.display_upper(lower, upper):
                                        - 
                                        ${facet.get_value(upper)} 
                                    % endif
                                    
                                % else:
                                    ${facet.get_value(lower)}+
                                % endif
                                </a>
                            </div>
                            <div class="span1">
                                (${count})
                            </div>
                        </div>
                    % endfor
                % endif
                <% date_range = False %>
            ## if this is a field or query facet, display as normal
            % else:
                <% other = True %>
                % for value, count in c['results'].get_ordered_facets(facet.field):
                    % if not c['results'].in_args(facet.field, value):
                        <div class="row">
                            <div class="span2">
                                <a href="${c['url_manager'].get_add_url(facet.field, value)}">
                                ${facet.get_value(value)} 
                                </a>
                            </div>
                            <div class="span1">
                                (${count})
                            </div>
                        </div>
                    % endif
                % endfor
                <% other = False %>
            % endif
            </div>
        
        ## if there are no values for this facet, display it without any values -->
        % else:
            <div class="empty_facet">
                <strong>${facet.display}</strong>
            </div>
        % endif
        </div>
    % endif
% endfor