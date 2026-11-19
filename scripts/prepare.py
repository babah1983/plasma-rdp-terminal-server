#!/usr/bin/env python3
"""Copy pinned upstream sources, then apply the lab patch series."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERIES = {
    'krdp-greeter-6.7.4': ['krdp-6.7.4.patch', 'krdp-6.7.4-button-position.patch'],
    'krdp-6.7.4': ['krdp-6.7.4.patch', 'krdp-6.7.4-display-control.patch', 'krdp-6.7.4-progressive-resize.patch', 'krdp-6.7.4-button-position.patch'],
    'plasma-login-manager-6.7.4': ['plasma-login-manager-6.7.4.patch'],
    'kpipewire-6.7.4': ['kpipewire-6.7.4-shared-memory.patch', 'kpipewire-6.7.4-encoder-lifetime.patch', 'kpipewire-6.7.4-frame-pool.patch'],
    'guacamole-server-1.6.0': ['guacamole-1.6.0-external-buffer-resize.patch'],
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/sources')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error(f'{output} already exists; use a new output directory')
    metadata = json.loads((ROOT / 'upstream-metadata.json').read_text())
    for line in (ROOT / 'upstream-files.sha256').read_text().splitlines():
        digest, relative = line.split('  ', 1)
        if hashlib.sha256((ROOT / metadata.get(relative, relative)).read_bytes()).hexdigest() != digest:
            raise SystemExit(f'Upstream snapshot changed: {relative}')
    for relative, target in json.loads((ROOT / 'upstream-links.json').read_text()).items():
        path = ROOT / relative
        if not path.is_symlink() or os.readlink(path) != target:
            raise SystemExit(f'Upstream link changed: {relative}')
    output.mkdir(parents=True)
    for component, patches in SERIES.items():
        target = output / component
        upstream = 'krdp-6.7.4' if component == 'krdp-greeter-6.7.4' else component
        shutil.copytree(ROOT / 'upstream' / upstream, target, symlinks=True)
        prefix = 'upstream/' + upstream + '/'
        for original, stored in metadata.items():
            if original.startswith(prefix):
                destination = target / original.removeprefix(prefix)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / stored, destination)
        for patch in patches:
            subprocess.run(['patch', '--batch', '-p1', '-i', str(ROOT / 'patches' / patch)], cwd=target, check=True)
    (output / 'applied-series.json').write_text(json.dumps(SERIES, indent=2) + '\n')
    print(f'Prepared patched sources: {output}')

if __name__ == '__main__':
    main()
