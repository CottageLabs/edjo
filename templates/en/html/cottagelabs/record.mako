<html>
<head>
    <link rel="stylesheet" type="text/css" href="/static/cottagelabs/styles.css"/>
    <script type="text/javascript" src="/static/lib/jquery.js"></script>
    <script>
    
    <%include file="/facets.js.mako"/>
    
    </script>
    <title>${c['config'].cottagelabs_service_title}</title>
</head>

<body>
    
    <%include file="/header.mako"/>
    
    <div id="panel">
    
        <%include file="/result-view.mako"/>
        
    </div>
    
    <%include file="/footer.mako"/>
    
</body>
</html>