import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from knowledge import build

async def main():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        (root/'manual.html').write_text('<h1 id="derive">NUOPC_CompDerive</h1><p>Derive component behavior.</p><h2>Signature</h2><pre>call NUOPC_CompDerive(model, rc=rc)</pre>')
        (root/'cap.F90').write_text('subroutine SetServices(model,rc)\n call NUOPC_CompDerive(model,rc=rc)\nend subroutine SetServices\n')
        manifest=root/'corpus.json'
        manifest.write_text(json.dumps({'sources':[{'name':'manual','path':'manual.html','kind':'documentation','version':'8.9.1'},
            {'name':'cap','path':'cap.F90','kind':'example','version':'8.9.1'}]}))
        db=root/'index.sqlite3';build(manifest,db)
        params=StdioServerParameters(command=sys.executable,args=[str(Path('server.py').resolve())],env={**os.environ,'DOCS_MCP_DB':str(db)})
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize(); tools=await session.list_tools()
                assert {t.name for t in tools.tools}=={'search_docs','search_code','get_section','get_routine','get_nuopc_context','list_sources','get_kokkos_context','list_collections'}
                async def call(name,args):
                    result=await session.call_tool(name,args);assert not result.isError,result
                    return result.structuredContent or json.loads(result.content[0].text)
                docs=await call('search_docs',{'query':'NUOPC_CompDerive'})
                docs=docs.get('result',docs) if isinstance(docs,dict) else docs
                section=await call('get_section',{'section_id':docs[0]['id']});assert 'call NUOPC_CompDerive' in section['text']
                code=await call('search_code',{'query':'SetServices'})
                code=code.get('result',code) if isinstance(code,dict) else code
                await call('get_routine',{'routine_id':code[0]['id']})
                await call('get_nuopc_context',{'query':'NUOPC_CompDerive','focus':'cap'})
                await call('list_sources',{})
                await call('list_collections',{})
                await call('get_kokkos_context',{'query':'parallel_for'})
                bad=await session.call_tool('search_docs',{'query':'NUOPC_CompDerive','version':'8.8.0'});assert bad.isError
        print('All eight MCP tools passed real stdio smoke test')

if __name__=='__main__':asyncio.run(main())
