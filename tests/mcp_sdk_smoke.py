"""Optional integration test: run with an environment containing the official mcp SDK."""
import asyncio
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters, stdio_client

async def main():
    root=Path(__file__).resolve().parents[1]
    params=StdioServerParameters(command=str(root/'dist/RetroSFX/RetroSFX.exe'),args=['--mcp'])
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            init=await session.initialize()
            print('Initialized:',init.server_info.name,init.protocol_version)
            listing=await session.list_tools()
            assert len(listing.tools)==6
            print('Tools:',[tool.name for tool in listing.tools])
            presets=await session.call_tool('list_presets',{})
            assert len(json.loads(presets.content[0].text)['presets'])==52
            preset=await session.call_tool('get_preset',{'index':51})
            assert not preset.is_error
            p=json.loads(preset.content[0].text);assert p['name']=='OPM / パワーアップ'
            p['name']='Official SDK template'
            result=await session.call_tool('export_sound',{'patch':p})
            assert not result.is_error,result
            data=json.loads(result.content[0].text)
            for path in data['files'].values():assert Path(path).is_file()
            print('Generated files:',len(data['files']))
            invalid=await session.call_tool('validate_patch',{'patch':{'duration':-1}})
            assert invalid.is_error
            print('Invalid patch rejected; SDK integration PASSED')

if __name__=='__main__':asyncio.run(main())
