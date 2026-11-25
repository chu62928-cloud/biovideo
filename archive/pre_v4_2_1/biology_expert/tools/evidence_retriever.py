"""Bounded real retrieval; HTTP 200 challenge pages do not count as evidence."""
from pathlib import Path
from urllib.parse import urlparse
import requests,json,re,time,hashlib,xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from ..state import write
CATALOG=[
 ('DNA replication eukaryotes DNA synthesis polymerase primer lagging','https://openstax.org/books/biology-2e/pages/14-5-dna-replication-in-eukaryotes'),
 ('DNA replication nucleotides template primer direction DNA synthesis','https://openstax.org/books/concepts-biology/pages/9-2-dna-replication'),
 ('mitosis eukaryotic cells chromosome sister chromatids metaphase anaphase cell cycle','https://openstax.org/books/biology-2e/pages/10-2-the-cell-cycle'),
 ('mitosis eukaryotic cells chromosome sister chromatids metaphase anaphase cell cycle','https://openstax.org/books/concepts-biology/pages/6-2-the-cell-cycle')]
ALLOWED={'openstax.org','www.ncbi.nlm.nih.gov','eutils.ncbi.nlm.nih.gov','pubmed.ncbi.nlm.nih.gov','pmc.ncbi.nlm.nih.gov'}
class EvidenceRetriever:
 def __init__(self,root,max_requests=24,timeout=18):
  self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
  self.path=self.root/'network.json';self.rows=json.loads(self.path.read_text()) if self.path.exists() else []
  self.max_requests=max_requests;self.timeout=timeout
 def get(self,url,params=None):
  if urlparse(url).hostname not in ALLOWED:raise ValueError('Untrusted source domain')
  if len(self.rows)>=self.max_requests:raise RuntimeError('Public retrieval budget exhausted')
  rec={'url':url,'params':params,'accessed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'status':'pending'}
  self.rows.append(rec);write(self.path,self.rows)
  try:
   r=requests.get(url,params=params,timeout=self.timeout,allow_redirects=False,headers={'User-Agent':'Code2BioVideoResearch/3.0 (educational provenance audit)'})
   rec.update(http_status=r.status_code,status='ok' if r.status_code==200 else 'UNVERIFIED')
   r.raise_for_status()
   if 300<=r.status_code<400:raise ValueError('Redirect requires separately validated destination')
   return r
  except Exception as ex:
   rec.update(status='UNVERIFIED',error_type=type(ex).__name__);raise
  finally:write(self.path,self.rows)
 def retrieve(self,scope):
  topic=scope['topic'];tokens=set(re.findall('[a-z]+',topic.lower()))-{'in','of','the','cells'}
  ranked=sorted(CATALOG,key=lambda x:-len(tokens&set(x[0].lower().split())))
  selected=[u for k,u in ranked[:2] if len(tokens&set(k.lower().split()))>=2]
  evidence=[];failures=[]
  for url in selected:
   try:
    r=self.get(url);r.encoding='utf-8';soup=BeautifulSoup(r.text,'html.parser')
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    for el in soup(['script','style','nav','footer','header']):el.decompose()
    txt=soup.get_text(' ',strip=True)
    if len(txt)<1000 or 'Checking your browser' in txt:raise ValueError('Non-content/challenge response')
    paragraphs=[p.get_text(' ',strip=True) for p in soup.find_all(['p','h2','h3']) if len(p.get_text(' ',strip=True))>=50]
    score=lambda p:sum(w in p.lower() for w in tokens)
    passages=sorted(paragraphs,key=score,reverse=True)[:12]
    # Save source content for evidence-location audit; OpenStax CC BY 4.0, attribution retained.
    eid='E_'+hashlib.sha256(url.encode()).hexdigest()[:10]
    (self.root/(eid+'.txt')).write_text(txt)
    evidence.append({'evidence_id':eid,'url':url,'title':title,'publisher':'OpenStax, Rice University','license':'CC BY 4.0; see source page; attribution required','accessed_utc':self.rows[-1]['accessed_utc'],'content_sha256':hashlib.sha256(txt.encode()).hexdigest(),'status':'RETRIEVED','passages':[{'location':f'paragraph selection {i+1}; exact text searchable in saved source','text':p[:1800]} for i,p in enumerate(passages)]})
   except Exception as ex:failures.append({'url':url,'status':'UNVERIFIED','error':type(ex).__name__})
  # Generic public search, beyond the small textbook discovery catalogue.
  try:
   q=topic+' AND (review[Publication Type])'
   data=self.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',{'db':'pubmed','term':q,'retmode':'json','retmax':2,'sort':'relevance'}).json()
   ids=data.get('esearchresult',{}).get('idlist',[])
   if ids:
    xml=self.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi',{'db':'pubmed','id':','.join(ids),'retmode':'xml'}).text
    for article in ET.fromstring(xml).findall('.//PubmedArticle'):
     pmid=article.findtext('.//PMID');title=''.join(article.find('.//ArticleTitle').itertext())
     abstract=' '.join(''.join(n.itertext()) for n in article.findall('.//AbstractText'))
     if len(abstract)<100:continue
     eid='PMID_'+pmid
     # Abstract excerpts bounded; claims still require verbatim supporting spans.
     evidence.append({'evidence_id':eid,'url':'https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/','title':title,'publisher':article.findtext('.//Journal/Title'),'license':'Publisher copyright; short research excerpts only','accessed_utc':self.rows[-1]['accessed_utc'],'status':'RETRIEVED','content_sha256':hashlib.sha256(abstract.encode()).hexdigest(),'passages':[{'location':'PubMed abstract','text':abstract[:2600]}]})
  except Exception as ex:failures.append({'source':'PubMed search','status':'UNVERIFIED','error':type(ex).__name__})
  write(self.root/(scope['topic_id']+'_retrieval.json'),{'evidence':evidence,'failures':failures})
  return {'evidence':evidence,'failures':failures,'research_status':'RETRIEVED' if evidence else 'UNVERIFIED','discovery':'Ranked source catalogue + live PubMed esearch/efetch; no model-created URL treated as retrieved'}

 def fetch_source(self,url):
  r=self.get(url);r.encoding='utf-8';soup=BeautifulSoup(r.text,'html.parser')
  title=soup.title.get_text(' ',strip=True) if soup.title else ''
  for el in soup(['script','style','nav','footer','header']):el.decompose()
  txt=soup.get_text(' ',strip=True)
  if len(txt)<1000 or 'Checking your browser' in txt:
   self.rows[-1].update(status='UNVERIFIED',reason='Challenge/non-content page')
   write(self.path,self.rows)
   return {'evidence':[],'failures':[{'url':url,'status':'UNVERIFIED','reason':'Challenge/non-content page'}]}
  eid='E_'+hashlib.sha256(url.encode()).hexdigest()[:10]
  (self.root/(eid+'.txt')).write_text(txt)
  passages=[{'location':'paragraph '+str(i+1),'text':el.get_text(' ',strip=True)} for i,el in enumerate(soup.find_all('p')) if len(el.get_text(' ',strip=True))>=40]
  ev={'evidence_id':eid,'url':url,'title':title,'publisher':'OpenStax, Rice University' if 'openstax.org' in url else 'NCBI Bookshelf','license':'CC BY 4.0 with attribution' if 'openstax.org' in url else 'Source-specific copyright; bounded excerpts','status':'RETRIEVED','content_sha256':hashlib.sha256(txt.encode()).hexdigest(),'accessed_utc':self.rows[-1]['accessed_utc'],'passages':passages}
  return {'evidence':[ev],'failures':[]}
