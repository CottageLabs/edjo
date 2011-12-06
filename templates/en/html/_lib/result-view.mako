<h2>Full Record Details</h2>

<table class="record_view" cellspacing="0">
% for field in c['config'].record:
    % for v in field.get_value_array(None, c['record']):
        <tr>
            <td><strong>${field.display}</strong></td>
            <td>${v}</td>
        </tr>
    % endfor
% endfor
</table>

<p><a href="${c['url_manager'].get_this_url()}">&laquo;Back to search results</a></p>
