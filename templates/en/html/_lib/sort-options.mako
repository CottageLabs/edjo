<div class="sort_options">

## first show the fields which are currently being sorted by
% if len(c['results'].current_sort_fields()) > 0:
    <div class="sort_label">
        Sorting by: 
    </div>
    % for sortby, direction in c['results'].current_sort_order():
        <div class="alert-message collapse-message search-constraint">
        ${c['config'].get_sort_option(sortby).display}
        % if direction == 'asc':
            <strong><span class="close unfloat selected-direction">^</span></strong> <a class="close unfloat" href="${c['url_manager'].get_sort_url(sortby, 'desc')}">v</a>
        % endif
        % if direction == 'desc':
            <a class="close unfloat" href="${c['url_manager'].get_sort_url(sortby, 'asc')}">^</a> <strong><span class="close unfloat selected-direction">v</span></strong>
        % endif
        <a class="close unfloat" href="${c['url_manager'].get_unsort_url(sortby)}">x</a>
        </div>
        <div class="sort_label">
            then
        </div>
    % endfor
% endif

## then show any remaining sort options
<%
    remaining = [s for s in c['config'].sort if s.field not in c['results'].current_sort_fields()]
%>
% if len(remaining) > 0:

    ## if there are no fields already being sorted by, put down a Sort By label
    % if len(c['results'].current_sort_fields()) == 0:
        <div class="sort_label">Sort by:</div>
    % endif

    % for sortby in remaining:
        <div class="potential_sort_option">
            ${sortby.display} (<a href="${c['url_manager'].get_sort_url(sortby.field, 'asc')}">^</a> 
                                <a href="${c['url_manager'].get_sort_url(sortby.field, 'desc')}">v</a>)
        </div>
    % endfor
% endif
</div>