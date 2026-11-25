from pathlib import Path
import json
from jsonschema import Draft202012Validator
BASE=Path(__file__).parent/'schemas'
def validate(kind,data):
 Draft202012Validator(json.loads((BASE/(kind+'.schema.json')).read_text())).validate(data)
 return data
