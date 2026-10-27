import json, os, re, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from openai import OpenAI

DAY = datetime.now(ZoneInfo("Asia/Kolkata"))
date = DAY.strftime("%Y-%m-%d")
name = DAY.strftime("%A, %d %B %Y")
path = Path("editions.json")
existing = json.loads(path.read_text()) if path.exists() else {}
if date in existing and os.getenv("FORCE_UPDATE") != "true":
    print(f"Already published {date}; preserving edition")
    sys.exit(0)
client = OpenAI()
prompt = f"""Today is {name} in India. Prepare an ORIGINAL and carefully sourced daily HR Intelligence Reader.
Audience: senior HR leader in India, especially IT, ITES, fintech and corporate employment. Current events must be verified using web search. Never invent laws, notifications, changes or hyperlinks. Clearly label ongoing rules, proposals, interpretations, country/state/factory-specific provisions, effective dates and uncertainty. If no materially new compliance rules, say so and teach one evergreen requirement. Never repeat an unverified claim from earlier reader editions.
Provide six named sections: HR Compliance — India, HR Compliance — EU, HR Technology — Global, HR Technology — India, HR News — Global, HR News — India. For India explain actual legal mandates and limitations, with PF, ESI, basic-pay versus wage definition, double wages/holiday wages, Form V-A, disciplinary/show cause, labour codes, Shops and Establishments as relevant. For EU distinguish directives from member state transposition, Working Time, GDPR, pay transparency, AI Act. HR technology include use, pros, cons, availability; HR news give practical implications. Add 'Knowledge Library records' as seventh section with stable record identifiers, legal title, jurisdiction, coverage, factory-only or corporate, status, dates, HR action and official source URL. Prefer official websites for regulatory sources. Provide about 100-200 words per section and 350-450 words for the read-aloud script.
Output ONLY JSON object with these exact keys:
{{"title": "{name}", "brief": "natural 3-minute spoken summary", "sections": [["HR Compliance — India","..."],["HR Compliance — EU","..."],["HR Technology — Global","..."],["HR Technology — India","..."],["HR News — Global","..."],["HR News — India","..."],["Knowledge Library records","..."]], "links": [["Readable official/source title","https://real-source.example/path"], ...]}}.
All source URLs in links must be real sources found using web search, not constructed, and in any high-impact claims also mention source title and effective date in section text. No markdown, no citations tokens, no code fences."""
response = client.responses.create(model=os.getenv('OPENAI_MODEL','gpt-5.5'),tools=[{"type":"web_search"}],input=prompt)
raw=response.output_text.strip()
if raw.startswith('```'):
    raw=re.sub(r'^```(?:json)?\s*|\s*```$', '',raw)
item=json.loads(raw)
if not isinstance(item.get('sections'),list) or len(item['sections'])!=7:raise RuntimeError('Invalid section structure: refusing publication')
if any(not isinstance(s,list) or len(s)!=2 or len(s[1])<100 for s in item['sections']):raise RuntimeError('Missing narrative: refusing publication')
if len(item.get('brief',''))<400:raise RuntimeError('Missing audio summary: refusing publication')
if len(item.get('links',[]))<4:raise RuntimeError('Insufficient source links: refusing publication')
for label,url in item['links']:
    if not re.match(r'^https://[^\s]+$',url):raise RuntimeError('Invalid source link: refusing publication')
item['title']=name
existing[date]=item
path.write_text(json.dumps(dict(sorted(existing.items(),reverse=True)),ensure_ascii=False,indent=2)+'\n')
print(f'Generated {date} with {len(item["links"])} links; editorial review recommended for statutory claims')
