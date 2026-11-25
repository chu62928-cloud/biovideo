"""Repository-root entrypoint selecting canonical V4.2.1 source explicitly."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'Code2Video/src'))
from biology_expert.contract_cli import main
if __name__=='__main__':raise SystemExit(main())
