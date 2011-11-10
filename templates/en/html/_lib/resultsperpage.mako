<div class="results_per_page">

    <div class="rpp_label">Results per page: </div>
% for rpp in c['config'].bruce_results_per_page_options:
%   if rpp == c['results'].page_size():
    <div class="current_rpp">${rpp}</div>
%   else:
    <div class="potential_rpp"><a href="${c['url_manager'].get_rpp_url(rpp)}">${rpp}</a></div>
%   endif
% endfor

</div>