#!/usr/bin/env python3
"""Turn a libretro/glsl-shaders preset into a Play Room shader entry with tools/rotk-enhance.glsl as pass 0.

  python3 tools/mkshader.py scalefx scalefx/scalefx.glslp   # writes preset-scalefx.json
"""
R='/home/user/libretro/glsl-shaders'
def build(preset_path):
    d=os.path.dirname(preset_path)
    kv={}
    for line in open(preset_path):
        m=re.match(r'\s*(\w+)\s*=\s*"?([^"\n]*)"?',line)
        if m: kv[m.group(1)]=m.group(2).strip()
    n=int(kv['shaders'])
    out=['shaders = %d'%(n+1),'','shader0 = rotk-enhance.glsl','filter_linear0 = false','scale_type0 = source','scale0 = 1.0','']
    res={}
    for i in range(n):
        for k,v in kv.items():
            m=re.match(r'(\w+?)(\d+)$',k)
            if m and int(m.group(2))==i:
                key=m.group(1)
                if key=='shader':
                    src=os.path.normpath(os.path.join(d,v)); name=os.path.basename(src); res[name]=open(src).read(); v=name
                out.append('%s%d = %s'%(key,i+1,v))
        out.append('')
    return '\n'.join(out), res
name,path=sys.argv[1],sys.argv[2]
glslp,res=build(os.path.join(R,path))
print(glslp, file=sys.stderr)
obj={'shader':{'type':'text','value':glslp},'resources':[{'name':k,'type':'base64','value':base64.b64encode(v.encode()).decode()} for k,v in res.items()]}
json.dump(obj,open('preset-%s.json'%name,'w'))
print(name, sum(len(r['value']) for r in obj['resources']))
