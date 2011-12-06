<% if c['results'].set_size() == 0:
    return
%>

<table class="data_table" cellspacing="0">
    <tr>
        <th></th>
% for field in c['config'].fields:
        <th>
            <strong>${field.display}</strong>
        </th>
% endfor
    </tr>
% for i in range(len(c['results'].set())):
    <tr class="${'odd' if i % 2 == 0 else 'even'}">
    <td>
        <a href="${c['url_manager'].get_record_url(c['results'].set()[i])}">&raquo;</a>
    </td>
    % for field in c['config'].fields:
        <%
            value = field.get_value(c['results'].args, c['results'].set()[i])
        %>
        <td>
        % if value is not None:
            ${value}
        % else:
            -
        % endif
        </td>
    % endfor
    </tr>
% endfor

</table>
