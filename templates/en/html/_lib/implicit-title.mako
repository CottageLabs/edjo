<div class="implicit_title">
    % for field in c['implicit_facets'].keys():
        <%
            facet = c['config'].get_facet(field)
        %>
        <h1>
            ${facet.display} :
            ${", ".join([facet.get_value(x) for x in c['implicit_facets'][field]])}
        </h1>
    % endfor
</div>