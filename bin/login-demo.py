#!/usr/bin/env python3
"""Exercise Casdoor OAuth code flow and CSGHub callback for the local demo account."""
import http.cookiejar,json,pathlib,urllib.request,urllib.parse
root=pathlib.Path(__file__).resolve().parents[1]
creds=json.loads((root/'deploy/dev/credentials.json').read_text())
cookies=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(cookies))
params=urllib.parse.urlencode({'clientId':'7a97bc5168cb75ffc514','responseType':'code','redirectUri':'http://127.0.0.1:18080/api/v1/callback/casdoor','scope':'read','state':'casdoor'})
body={'type':'code','organization':'OpenCSG','application':'CSGHub','username':creds['username'],'password':creds['password'],'signinMethod':'Password'}
req=urllib.request.Request('http://127.0.0.1:18000/api/login?'+params,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
with opener.open(req,timeout=30) as response: result=json.load(response)
if result.get('status')!='ok':raise SystemExit('Login failed: '+str(result))
code=result['data']
if isinstance(code,dict): code=code.get('code')
url='http://127.0.0.1:18080/api/v1/callback/casdoor?'+urllib.parse.urlencode({'code':code,'state':'casdoor'})
with opener.open(url,timeout=60) as response:
 print('OAuth callback:',response.status,'Final page:',response.url.split('?')[0])
 if response.status!=200 or '/errors/' in response.url: raise SystemExit('Callback did not reach the Portal')
print('Demo account OAuth login successful')
