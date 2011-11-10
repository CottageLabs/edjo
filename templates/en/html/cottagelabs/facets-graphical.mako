% for facet in c['config'].facets:

    ## we don't process implicit facets, they are immutable -->
    % if facet.field not in c['implicit_facets']:
        <% f = facet.field %>
        ## a div to contain each facet -->
        <div class="facet">
        ## if the facet has values in the result set, display it and its facet values -->
        % if c['results'].has_values(facet.field):
        
            ## facet name, using its display form -->
            <div class="facet_heading">
                <a href="" id="fh_${facet.field}">+&nbsp;${facet.display}</a>
            </div>
            
            ## first display the facet values which have already been selected -->
            <div id="selected_${facet.field}" class="facet_value">
            
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
                        (${c['results'].numFound()})
                        </em>
                    % else:
                        <em>${facet.get_value(lower)}+ (${c['results'].numFound()})</em>
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
                        (${c['results'].numFound()})
                        </em>
                    % else:
                        <em>${facet.get_value(lower)}+ (${c['results'].numFound()})</em>
                    % endif
                    &nbsp;<a class="delete_url" href="${c['url_manager'].get_delete_url(facet.field)}">x</a><br/>
                % endif 
                <% date_range = False %>
            ## if this is a field facet or a query facet, there can be more than
            ## one value, so we treat these slightly differently
            % else:
                % for value, count in c['results'].get_ordered_facets(facet.field):
                    % if c['results'].in_args(facet.field, value):
                        <em>${facet.get_value(value)}</em>
                        &nbsp;<a class="delete_url" href="${c['url_manager'].get_delete_url(facet.field, value)}">x</a>
                        <br/>
                    % endif
                % endfor
            % endif
            </div>
            
            ## next display the facet values which are available to be selected -->
            <div id="fr_${facet.field}" style="display:none" class="facet_value"></div>
            
            ## if this is a range facet, display the available ranges
            % if c['config'].is_range_facet(facet.field):
                <% range = True %>
                ## only display options if this facet is not already selected
                % if not c['results'].in_args(facet.field):
                    % for lower, upper, count in c['results'].get_ordered_facets(facet.field):
                        <a href="${c['url_manager'].get_add_url(facet.field, lower, upper)}">
                        % if upper != -1:
                            ${facet.get_value(lower)} - ${facet.get_value(upper)} (${count})
                        % else:
                            ${facet.get_value(lower)}+ (${count})
                        % endif
                        </a><br/>
                    % endfor
                % endif
                <% range = False %>
            ## if this is a date facet, display the available ranges
            % elif c['config'].is_date_facet(facet.field):
                <% date_range = True %>
                ## only display options if this facet is not already selected
                % if not c['results'].in_args(facet.field):
                    % for lower, upper, count in c['results'].get_ordered_facets(facet.field):
                        <a href="${c['url_manager'].get_add_date_url(facet.field, lower, upper)}">
                        % if upper != -1:
                            ${facet.get_value(lower)}
                            % if facet.display_upper(lower, upper):
                                - 
                                ${facet.get_value(upper)} 
                            % endif
                            (${count})
                        % else:
                            ${facet.get_value(lower)}+ (${count})
                        % endif
                        </a><br/>
                    % endfor
                % endif
                <% date_range = False %>
            ## if this is a field or query facet, display as a graph
            % else:
                
            <script type="text/javascript">
            
            var counts = [
            <% first = True %>
            % for value, count in c['results'].get_ordered_facets(facet.field):
                % if not first:
                    ,
                % endif
                ${count}
                <% first = False %>
            % endfor
            ]
            
            var names = [
            <% first = True %>
            % for value, count in c['results'].get_ordered_facets(facet.field):
                % if not first:
                    ,
                % endif
                "${facet.get_value(value)}"
                <% first = False %>
            % endfor
            ]
            
            var offset = 50;
            var height = counts.length * 20;
            var width = 440 + offset;

            var chart = d3.select("div#fr_${facet.field}")
                        .append("svg:svg")
                        .attr("class", "chart")
                        .attr("width", width)
                        .attr("height", height)
                        .append("svg:g");

            var x = d3.scale.linear()
                        .domain([0, d3.max(counts)])
                        .range([offset, 420 + offset]);

            var y = d3.scale.ordinal()
                        .domain(counts)
                        .rangeBands([0, height]);

            chart.selectAll("rect.bar")
                    .data(counts)
                    .enter().append("svg:rect")
                    .attr("class", "bar")
                    .attr("x", offset)
                    .attr("y", function(d, i) { return i * 20; })
                    .attr("width", x)
                    .attr("height", 20);
            
            chart.selectAll("text.facet_counts")
                    .data(counts)
                    .enter().append("svg:text")
                    .attr("class", "facet_counts")
                    .attr("x", x)
                    .attr("y", function(d, i) { return i * 20 + 10; })
                    .attr("dx", -3) // padding-right
                    .attr("dy", ".35em") // vertical-align: middle
                    .attr("text-anchor", "end") // text-align: right
                    .text(String);
            
            chart.selectAll("text.facet_names")
                .data(names)
                .enter().append("svg:text")
                .attr("class", "facet_names")
                .attr("x", 0)
                .attr("y", function(d, i) { return i * 20 + 10; })
                .text(String);
            
            chart.selectAll("line")
                    .data(x.ticks(10))
                    .enter().append("svg:line")
                    .attr("x1", x)
                    .attr("x2", x)
                    .attr("y1", 0)
                    .attr("y2", height)
                    .attr("stroke", "#ccc");
                    
            chart.selectAll("text.rule")
                    .data(x.ticks(10))
                    .enter().append("svg:text")
                    .attr("class", "rule")
                    .attr("x", x)
                    .attr("y", 0)
                    .attr("dy", -3)
                    .attr("text-anchor", "middle")
                    .text(String);
                    
            chart.append("svg:line")
                    .attr("x1", offset)
                    .attr("x2", offset)
                    .attr("y1", 0)
                    .attr("y2", height)
                    .attr("stroke", "#000");

            </script>
                
            % endif
        
        ## if there are no values for this facet, display it without any values -->
        % else:
            <div class="empty_facet">
                <strong>${facet.display}</strong>
            </div>
        % endif
        </div>
    % endif
% endfor