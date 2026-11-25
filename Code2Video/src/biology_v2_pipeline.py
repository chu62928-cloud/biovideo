"""Transactional full-render gate and object-based AST repair boundary."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path('/autodl-tmp/code2biovideo').resolve()
ENV = ROOT / 'env'
EXPERIMENT = ROOT / 'Code2Video/experiments/biology_v2_section4'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safety_check(code):
    tree = ast.parse(code)
    allowed = {'manim', 'numpy', 'biology_runtime', 'math'}
    denied = {'exec', 'eval', 'compile', 'open', '__import__', 'getattr', 'setattr',
              'breakpoint', 'input', 'globals', 'locals'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(x.name.split('.')[0] in allowed for x in node.names), 'Import denied'
        if isinstance(node, ast.ImportFrom):
            assert (node.module or '').split('.')[0] in allowed, 'Import denied'
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in denied, 'Unsafe call: ' + node.func.id
        if isinstance(node, ast.Attribute):
            assert not node.attr.startswith('__'), 'Dunder access denied'
    assert any(isinstance(x, ast.ClassDef) and x.name == 'Section4Scene' for x in tree.body), 'Missing Section4Scene'
    return tree


def validate_issues(issues, known_ids):
    required = {'object_id', 'issue_type', 'current_state', 'target_constraint', 'suggested_change'}
    for issue in issues:
        assert required <= issue.keys(), 'Incomplete object issue'
        assert issue['object_id'] in known_ids, 'Unknown object ID: ' + str(issue['object_id'])
    return issues


def replace_construct(code, function_source):
    tree = safety_check(code)
    incoming = ast.parse(function_source)
    assert len(incoming.body) == 1 and isinstance(incoming.body[0], ast.FunctionDef)
    new = incoming.body[0]
    assert new.name == 'construct', 'Only construct function repair is accepted'
    target = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == 'Section4Scene')
    index = next(i for i, x in enumerate(target.body) if isinstance(x, ast.FunctionDef) and x.name == 'construct')
    target.body[index] = new
    result = ast.unparse(ast.fix_missing_locations(tree)) + '\n'
    safety_check(result)
    return result


def probe(video):
    return json.loads(subprocess.check_output([str(ENV/'bin/ffprobe'), '-v', 'error',
        '-show_format', '-show_streams', '-of', 'json', str(video)], text=True))


def trace_metrics(trace):
    frames = trace.get('frames', [])
    out_of_frame, overlaps, relations, jumps = [], [], [], []
    prior = {}
    for frame in frames:
        objects = frame['objects']
        labels = []
        for name, obj in objects.items():
            if not obj.get('visible'): continue
            lo, hi = obj['bbox']
            if lo[0] < -7.111-.05 or hi[0] > 7.111+.05 or lo[1] < -4.05 or hi[1] > 4.05:
                out_of_frame.append({'time': frame['time'], 'object': name})
            if obj.get('role') == 'label': labels.append((name, lo, hi))
            if name in prior:
                t, p = prior[name]; dt = frame['time']-t
                distance = sum((a-b)**2 for a,b in zip(obj['center'],p))**.5
                if dt > 0 and distance > 2 and dt < .4:
                    jumps.append({'time': frame['time'], 'object': name, 'distance': distance})
            prior[name] = (frame['time'], obj['center'])
        for i,(a,al,ah) in enumerate(labels):
            for b,bl,bh in labels[i+1:]:
                ix = min(ah[0],bh[0])-max(al[0],bl[0]); iy = min(ah[1],bh[1])-max(al[1],bl[1])
                if ix > .06 and iy > .06: overlaps.append({'time':frame['time'],'objects':[a,b]})
        for bind in frame.get('bindings', trace.get('bindings', [])):
            a,b = objects.get(bind['object_id']),objects.get(bind['target_id'])
            if a and b and a.get('visible'):
                distance = sum((x-y)**2 for x,y in zip(a['center'],b['center']))**.5
                if distance > bind['max_distance']+.1:
                    relations.append({'time':frame['time'],'object':bind['object_id'],'distance':distance})
    return {'out_of_frame':out_of_frame,'label_overlaps':overlaps,'binding_violations':relations,
            'sudden_jumps':jumps,'note':'Geometry heuristics; intentional occlusion and fade transitions need human review.'}


class TransactionRenderer:
    def __init__(self, group, runtime_file, assets=None, duration_range=None):
        self.group = Path(group); self.group.mkdir(parents=True,exist_ok=True)
        self.runtime_file = Path(runtime_file); self.assets = Path(assets) if assets else None
        self.duration_range = duration_range

    def state(self):
        pointer = self.group/'current'
        if not pointer.exists(): return None
        version = pointer.resolve()
        data = json.loads((version/'status.json').read_text())
        assert sha(version/'rendered_code.py') == data['code_sha256'], 'Code hash mismatch'
        assert sha(version/'video.mp4') == data['video_sha256'], 'Video hash mismatch'
        return {**data,'version':str(version),'code':str(version/'rendered_code.py'),'video':str(version/'video.mp4')}

    def attempt(self, code, tag, extra_validator=None):
        before = self.state()
        stage = self.group/'attempts'/tag
        stage.mkdir(parents=True,exist_ok=False)
        (stage/'candidate_code.py').write_text(code)
        result = {'tag':tag,'committed':False,'before':before,'started':time.time()}
        started = time.monotonic()
        try:
            safety_check(code)
            shutil.copy2(self.runtime_file,stage/'biology_runtime.py')
            if self.assets: shutil.copytree(self.assets,stage/'assets')
            (stage/'rendered_code.py').write_text(code)
            cp = subprocess.run([str(ENV/'bin/python'),str(ROOT/'sandbox_exec.py'),str(stage),
                'manim','-ql','--disable_caching','rendered_code.py','Section4Scene'],capture_output=True,text=True,timeout=180)
            (stage/'stdout.log').write_text(cp.stdout);(stage/'stderr.log').write_text(cp.stderr)
            assert cp.returncode == 0, 'Full Manim render failed; see stderr.log'
            video = stage/'media/videos/rendered_code/480p15/Section4Scene.mp4'
            meta = probe(video);duration = float(meta['format']['duration'])
            assert duration > .1, 'Missing or empty video'
            if self.duration_range: assert self.duration_range[0] <= duration <= self.duration_range[1], 'Duration outside requested range'
            decode = subprocess.run([str(ENV/'bin/ffmpeg'),'-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True,timeout=60)
            (stage/'decode.log').write_text(decode.stderr)
            assert decode.returncode == 0 and not decode.stderr.strip(), 'Video decode failed'
            trace = json.loads((stage/'geometry_trace.json').read_text()) if (stage/'geometry_trace.json').exists() else {}
            layout = trace_metrics(trace)
            (stage/'layout_metrics.json').write_text(json.dumps(layout,indent=2))
            if extra_validator: extra_validator(stage,trace,layout)
            shutil.copy2(video,stage/'video.mp4')
            manifest = {'success':True,'tag':tag,'code_sha256':sha(stage/'rendered_code.py'),
                        'video_sha256':sha(stage/'video.mp4'),'duration_seconds':duration,'renderer':'manim-0.19.0-full-render',
                        'trace_sha256':sha(stage/'geometry_trace.json') if trace else None}
            (stage/'status.json').write_text(json.dumps(manifest,indent=2))
            # One atomic directory-pointer commit publishes the matching immutable pair.
            versions = self.group/'versions';versions.mkdir(exist_ok=True)
            dest = versions/tag
            os.replace(stage,dest)
            tmp = self.group/'.next';tmp.symlink_to(dest.relative_to(self.group),target_is_directory=True)
            os.replace(tmp,self.group/'current')
            for name in ['rendered_code.py','video.mp4','status.json']:
                p=self.group/name
                if not p.is_symlink():
                    if p.exists(): p.unlink()
                    p.symlink_to('current/'+name)
            result.update(committed=True,after=self.state())
        except Exception as exc:
            result.update(error_type=type(exc).__name__,error=str(exc),after=self.state())
            assert result['after'] == before, 'Rollback failed'
            if not before and not (self.group/'status.json').exists():
                (self.group/'status.json').write_text(json.dumps({'success':False,'error':str(exc)},indent=2))
            (stage/'failure.json').write_text(json.dumps(result,indent=2))
        result['elapsed_seconds'] = round(time.monotonic()-started,3)
        (self.group/(tag+'_transaction.json')).write_text(json.dumps(result,indent=2))
        return result
