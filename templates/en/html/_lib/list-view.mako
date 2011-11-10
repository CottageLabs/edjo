<% if c['results'].set_size() == 0:
    return
%>

<div class="list_view">
    % for i in range(len(c['results'].set())):
        <div class="list_result_${'odd' if i % 2 == 0 else 'even'}">
            % for field in c['config'].fields:
                <%
                    value = field.get_value(c['results'].args, c['results'].set()[i])
                %>
                % if value != "":
                    <div class="list_result_field">${value}</div>
                % endif
            % endfor
        </div>
    % endfor
</div>
