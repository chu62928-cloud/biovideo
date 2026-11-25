"""Linux Landlock + seccomp renderer. Fail closed; never inherit credentials."""
import ctypes, errno, os, resource, sys
from pathlib import Path

ROOT=Path('/root/autodl-tmp/code2biovideo')
ENV=ROOT/'env'
TEX=ROOT/'texlive'
UID=62001

def checked(value, label):
    if value < 0:
        raise OSError(ctypes.get_errno(), label)
    return value

def main():
    cwd=Path(sys.argv[1]).resolve()
    assert ROOT in cwd.parents
    cmd=sys.argv[2:]
    assert cmd and cmd[0] in ('manim','python')
    os.chdir(cwd)
    for p in [cwd,*cwd.rglob('*')]:
        if not p.is_symlink(): os.chown(p,UID,UID)
    libc=ctypes.CDLL(None,use_errno=True)
    # Named-user ACL grants only traversal of /root, never listing or reading it.
    acl=ctypes.CDLL('libacl.so.1',use_errno=True)
    acl.acl_from_text.argtypes=[ctypes.c_char_p]; acl.acl_from_text.restype=ctypes.c_void_p
    acl.acl_set_file.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.c_void_p]
    acl.acl_free.argtypes=[ctypes.c_void_p]
    obj=acl.acl_from_text(b'user::rwx,user:62001:--x,group::---,mask::--x,other::---')
    checked(acl.acl_set_file(b'/root',0x8000,obj),'ACL traversal'); acl.acl_free(obj)
    # Landlock ABI 1 covers reads, writes, execution and directory creation/removal.
    class Ruleset(ctypes.Structure): _fields_=[('access',ctypes.c_uint64)]
    class Beneath(ctypes.Structure):
        _pack_=1
        _fields_=[('access',ctypes.c_uint64),('parent_fd',ctypes.c_int32)]
    handled=(1<<13)-1
    fd=checked(libc.syscall(444,ctypes.byref(Ruleset(handled)),8,0),'landlock_create')
    ro=(1<<0)|(1<<2)|(1<<3)
    rules=[(ENV,ro),(cwd,handled)]
    if TEX.exists(): rules.append((TEX,ro))
    for p in ['/usr','/lib','/lib64','/bin','/sbin','/etc/fonts','/etc/ld.so.cache','/etc/localtime','/dev/urandom','/dev/random','/proc/cpuinfo','/proc/meminfo','/proc/stat','/proc/self']:
        if Path(p).exists(): rules.append((Path(p),ro))
    rules.append((Path('/dev/null'),(1<<1)|(1<<2)))
    for p,access in rules:
        if not p.is_dir(): access &= ~8
        pfd=os.open(p,os.O_PATH|os.O_CLOEXEC)
        checked(libc.syscall(445,fd,1,ctypes.byref(Beneath(access,pfd)),0),'landlock_add '+str(p))
        os.close(pfd)
    checked(libc.prctl(38,1,0,0,0),'no_new_privs')
    checked(libc.syscall(446,fd,0),'landlock_restrict');os.close(fd)
    # Deny networking, tracing, namespace/mount and privilege changes; inherited by children.
    sec=ctypes.CDLL('libseccomp.so.2',use_errno=True)
    sec.seccomp_init.argtypes=[ctypes.c_uint32];sec.seccomp_init.restype=ctypes.c_void_p
    sec.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p]
    sec.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
    sec.seccomp_load.argtypes=[ctypes.c_void_p]
    ctx=sec.seccomp_init(0x7fff0000)
    for name in ['socket','connect','bind','listen','accept','accept4','ptrace','process_vm_readv','process_vm_writev','mount','umount2','unshare','setns','bpf','keyctl','open_by_handle_at']:
        num=sec.seccomp_syscall_resolve_name(name.encode())
        if num>=0: checked(sec.seccomp_rule_add(ctx,0x50000|errno.EPERM,num,0),'seccomp '+name)
    checked(sec.seccomp_load(ctx),'seccomp_load')
    os.setgroups([]);os.setgid(UID);os.setuid(UID)
    resource.setrlimit(resource.RLIMIT_CPU,(160,170))
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(1024**3,1024**3))
    resource.setrlimit(resource.RLIMIT_NPROC,(64,64))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    env={'PATH':str(TEX/'bin/x86_64-linux')+':'+str(ENV/'bin')+':/usr/bin:/bin','HOME':str(cwd),'TMPDIR':str(cwd),
         'LANG':'C.UTF-8','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1',
         'XDG_CACHE_HOME':str(cwd/'.cache'),'PYTHONNOUSERSITE':'1'}
    os.execve(str(ENV/'bin'/cmd[0]),cmd,env)

if __name__=='__main__': main()
