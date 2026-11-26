"""Scientific context for the upstream Planner and Coder, with isolated rendering."""
import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from .contracts import digest, write


class Code2VideoAdapter:
    def __init__(self, root, request, context, gateway):
        from agent import RunConfig, TeachingVideoAgent

        self.root = root
        self.context = context
        self.phase = 'planning'
        self.feedback = ''
        base = root / 'upstream'
        (base / 'assets').mkdir(parents=True, exist_ok=True)
        (base / 'json_files').mkdir(exist_ok=True)
        write(base / 'json_files/long_video_ref_mapping.json', {})
        write(root / 'generation_context.json', {'sha256': digest(context), 'context': context})

        def api(prompt, **kwargs):
            if not isinstance(prompt, str):
                raise ValueError('Upstream prompt must be text')
            prompt += '\n\nRequired production context:\n' + json.dumps(context, ensure_ascii=False)
            prompt += ('\nUse no external assets or TeX. Use plain Manim Text. '
                       'Return exactly one standalone lesson section covering every required claim. '
                       'Show dynamic mechanisms through motion or changing geometry, synchronized with labels. '
                       'Keep all text and objects in frame. Target the specified total duration.')
            if self.feedback:
                prompt += '\nRevise only this scene, preserving its claim IDs and adjacent continuity:\n' + self.feedback
            value = gateway.request('deepseek', 'v51_' + self.phase, prompt)
            response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=value))])
            return response, {}

        config = RunConfig(api=api, use_assets=False, use_feedback=False, max_regenerate_tries=1)
        self.agent = TeachingVideoAgent(0, request, folder=str(base / 'CASES'), cfg=config)

    def plan(self):
        self.agent.generate_outline()
        sections = self.agent.generate_storyboard()
        if len(sections) != 1:
            # Consolidate upstream beats into the one continuous short lesson requested.
            from agent import Section
            sections = [Section(id='section_1', title='Complete lesson', lecture_lines=[
                text for section in sections for text in section.lecture_lines
            ], animations=[text for section in sections for text in section.animations])]
        sections[0].id = 'section_1'
        return sections[0]

    def code(self, section, feedback=''):
        self.phase = 'repair' if feedback else 'generation'
        self.feedback = feedback
        if feedback:
            self.feedback += '\nOriginal scene code:\n' + self.agent.section_codes.get(section.id, '')
        return self.agent.generate_section_code(section, attempt=2 if feedback else 1)


def render(root, code, name):
    folder = root / 'generated_code' / name
    folder.mkdir(parents=True, exist_ok=False)
    (folder / 'lesson.py').write_text(code)
    try:
        classes = [node.name for node in ast.parse(code).body if isinstance(node, ast.ClassDef)
                   and any(isinstance(f, ast.FunctionDef) and f.name == 'construct' for f in node.body)]
        if len(classes) != 1:
            raise ValueError('Expected one concrete Manim class')
        base = Path('/autodl-tmp/code2biovideo')
        cp = subprocess.run([sys.executable, str(base/'sandbox_exec.py'), str(folder), 'manim',
                             '-qm', '--disable_caching', 'lesson.py', classes[0]],
                            capture_output=True, timeout=160)
        (folder/'render.log').write_bytes(cp.stdout + cp.stderr)
        if cp.returncode:
            raise RuntimeError(cp.stderr.decode(errors='replace')[-1100:])
        video = next((folder/'media').rglob(classes[0]+'.mp4'), None)
        if video is None:
            raise RuntimeError('Manim rendered no MP4')
        target = root / ('candidate_' + name + '.mp4')
        shutil.copyfile(video, target)
        probe(target)
        return target
    except Exception as exc:
        (folder/'failure.txt').write_text(str(exc))
        raise


def probe(path):
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'],
                   check=True, capture_output=True, timeout=65)
    value = subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format',
                                     '-of','json',str(path)], timeout=20)
    data = json.loads(value)
    stream = next(s for s in data['streams'] if s['codec_type']=='video')
    return dict(duration=float(data['format']['duration']), width=stream['width'],
                height=stream['height'], fps=stream['avg_frame_rate'])
