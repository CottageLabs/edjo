<html>
<head>
    <link rel="stylesheet" type="text/css" href="/static/cottagelabs/styles.css"/>
    <script type="text/javascript" src="/static/lib/jquery.js"></script>
    <script type="text/javascript" src="/static/lib/d3/d3.js"></script>
    <script>
    
    <%include file="/facets.js.mako"/>
    
    </script>
    <title>${c['config'].cottagelabs_service_title}</title>
</head>

<body>
    
    <%include file="/header.mako"/>
    
    <div id="navigation">
        <%include file="/facets-graphical.mako"/>
    </div>
    
    <div id="panel">
    
        <%include file="/implicit-title.mako"/>
        % if c['config'].allow_text_search:
            <%include file="/search-box.mako"/>
        % endif
        <%include file="/search-summary.mako"/>
            
        % if c['results'].set_size() == 0:
            <%include file="/noresults.mako"/>
        % else:
            <%include file="/sort-options.mako"/>
            <%include file="/paging.mako"/>
            <%include file="/resultsperpage.mako"/>
            <div class="result_view">
                <%include file="/table-view.mako"/>
            </div>
        
        % endif

    </div>
    
    <%include file="/footer.mako"/>
    
</body>
</html>