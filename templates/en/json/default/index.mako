[
% for i in range(len(c['results'].set())):
{
    <% first = True %>
    % for field in c['config'].fields:
        % if not first:
            ,
        % endif
        <% first = False %>
        "${field.field}" : "${field.get_value(c['results'].args, c['results'].set()[i])}"
    % endfor
}
% endfor
]