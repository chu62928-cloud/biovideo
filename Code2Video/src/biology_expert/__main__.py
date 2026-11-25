import sys
if sys.argv[1:2]==['contract']:
 from .contract_cli import main
 raise SystemExit(main(sys.argv[2:]))
raise SystemExit('Legacy default workflow retired. Use: python audit_contract.py audit --contract ... --scene ... --output ... (offline)')
