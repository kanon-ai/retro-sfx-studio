import sys
if '--mcp' in sys.argv:
    import mcp_server
    mcp_server.main()
else:
    import server
    server.main()
