<% if c['results'].set_size() == 0:
    return
%>

<table class="data_table" cellspacing="0">
    <tr>
% for field in c['config'].fields:
        <th>
            <strong>${field.display}</strong>
        </th>
% endfor
    </tr>
% for i in range(len(c['results'].set())):
    <tr class="${'odd' if i % 2 == 0 else 'even'}">
    % for field in c['config'].fields:
        <td>
            ${field.get_value(c['results'].args, c['results'].set()[i])}
        </td>
    % endfor
    </tr>
% endfor

</table>
