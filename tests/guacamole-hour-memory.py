#!/usr/bin/env python3
"""Read-only monotonic one-hour KRdp collector. Run as root in the test VM."""
import csv, datetime, os, subprocess, sys, time

duration = float(sys.argv[1]) if len(sys.argv) > 1 else 3600
start = time.monotonic()
writer = csv.writer(sys.stdout)
writer.writerow(('utc','elapsed_s','user','pid','rss_kib','pss_kib','private_dirty_kib','threads','fds','cpu_ticks','kate_pid','kwin_pid'))
def pid_for(user, name):
    return subprocess.run(['pgrep','-u',user,'-x',name],capture_output=True,text=True).stdout.strip().replace('\n','|')
while True:
    elapsed = time.monotonic()-start
    for user in ('native-a','native-b'):
        pid = pid_for(user,'krdpserver')
        try:
            with open('/proc/'+pid+'/smaps_rollup') as f:
                mem={k:v.split()[0] for k,v in (line.split(':',1) for line in f if ':' in line)}
            with open('/proc/'+pid+'/status') as f:
                status={k:v.split()[0] for k,v in (line.split(':',1) for line in f if ':' in line) if v.split()}
            with open('/proc/'+pid+'/stat') as f:
                stat=f.read().rsplit(')',1)[1].split()
            writer.writerow((datetime.datetime.now(datetime.timezone.utc).isoformat(),round(elapsed,2),user,pid,mem['Rss'],mem['Pss'],mem['Private_Dirty'],status['Threads'],len(os.listdir('/proc/'+pid+'/fd')),int(stat[11])+int(stat[12]),pid_for(user,'kate'),pid_for(user,'kwin_wayland')))
        except (OSError, KeyError, ValueError) as exc:
            print(f'collector error {user}: {exc}',file=sys.stderr,flush=True)
    sys.stdout.flush()
    if elapsed >= duration:
        break
    time.sleep(min(10,duration-(time.monotonic()-start)) if time.monotonic()-start<duration else 0)
