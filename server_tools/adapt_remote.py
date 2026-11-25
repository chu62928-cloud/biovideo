from pathlib import Path
import subprocess, json, os
root = Path('/autodl-tmp/code2biovideo/Code2Video')
os.chdir(root)
# Restore exact upstream blob bytes after Windows checkout line ending conversion.
for name in subprocess.check_output(['git','ls-files'],text=True).splitlines():
    p=root/name
    if p.exists():
        p.write_bytes(subprocess.check_output(['git','show','HEAD:'+name]))
subprocess.run(['git','config','core.autocrlf','false'],check=True)
subprocess.run(['git','config','core.filemode','false'],check=True)
p=root/'src/gpt_request.py'
p.write_text(p.read_text()+'''

def request_deepseek_token(prompt, log_id=None, max_tokens=10000, max_retries=2):
    """OpenAI-compatible provider; all connection settings come from environment."""
    import uuid
    required = ("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL")
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise ValueError("Missing environment variables: " + ", ".join(missing))
    client = OpenAI(api_key=os.environ[required[0]], base_url=os.environ[required[1]],
                    max_retries=0, timeout=180)
    call_id = log_id or uuid.uuid4().hex
    audit_dir = pathlib.Path(os.environ.get("CODE2VIDEO_AUDIT_DIR", "deepseek_audit"))
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / (call_id + ".prompt.txt")).write_text(prompt, encoding="utf-8")
    for attempt in range(1, min(max_retries, 2) + 1):
        started = time.monotonic()
        record = {"call_id": call_id, "attempt": attempt, "provider": "deepseek",
                  "requested_model": os.environ[required[2]], "max_tokens": max_tokens,
                  "stage": os.environ.get("CODE2VIDEO_STAGE", "unknown"),
                  "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        try:
            response = client.chat.completions.create(
                model=os.environ[required[2]], messages=[{"role":"user", "content":prompt}],
                max_tokens=max_tokens)
            usage = response.usage.model_dump() if response.usage else {}
            record.update(status="ok", model=response.model, usage=usage,
                          finish_reason=response.choices[0].finish_reason)
            (audit_dir / (call_id + ".response.json")).write_text(response.model_dump_json(indent=2), encoding="utf-8")
            if response.choices[0].finish_reason == "length":
                raise ValueError("DeepSeek response truncated at token limit")
            return response, usage
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            record.update(status="error", error_type=type(exc).__name__, status_code=status_code)
            # Authentication, account, format and rate-limit failures stop immediately.
            if status_code in (400, 401, 402, 403, 404, 422, 429) or attempt >= min(max_retries, 2) or isinstance(exc, ValueError):
                raise
            time.sleep(1)
        finally:
            record["elapsed_seconds"] = round(time.monotonic() - started, 3)
            with (audit_dir / "requests.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\\n")
''',encoding='utf-8')
p=root/'src/agent.py'
s=p.read_text().replace('ScopeRefineFixer(api, self.max_code_token_length)','ScopeRefineFixer(self.API, self.max_code_token_length)')
s=s.replace('"gpt-41": (request_gpt41_token, "Chatgpt41"),','"deepseek": (request_deepseek_token, "DeepSeek"),\n        "gpt-41": (request_gpt41_token, "Chatgpt41"),')
s=s.replace('choices=["gpt-41",','choices=["deepseek", "gpt-41",')
s=s.replace('print(f"Iconfinder API Key: {args.iconfinder_api_key}")','print("Iconfinder API Key configured (value hidden)")')
p.write_text(s,encoding='utf-8')
# The upstream code resolves these paths under src despite the repository layout.
for name in ('prompts','json_files'):
    (root/'src'/name).symlink_to('../'+name,target_is_directory=True)
(root/'src/assets/icon').mkdir(parents=True,exist_ok=True)
exp=root/'experiments/biology_baseline'
for name in ('logs','previews','tests'):
    (exp/name).mkdir(parents=True,exist_ok=True)
env=Path('/autodl-tmp/code2biovideo/.env')
key=None
for line in Path('/root/autodl-tmp/my-fastapi/.env').read_text().splitlines():
    if line.startswith('DEEPSEEK_API_KEY='):
        key=line.split('=',1)[1].strip().strip('"').strip("'")
assert key
env.write_text('DEEPSEEK_API_KEY='+key+'\nDEEPSEEK_BASE_URL=https://api.deepseek.com\nDEEPSEEK_MODEL=deepseek-flash\n')
env.chmod(0o600)
with (exp/'upstream.patch').open('w') as f:
    subprocess.run(['git','diff','--','src'],stdout=f,check=True)
print('Provider added; secrets kept server-side. Upstream prompt files unchanged.')
