#!/usr/bin/env python3
"""Install the reviewed background clone; retain a dated configuration backup."""
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
HOME = Path.home()

def run(*args):
    subprocess.run(args, check=True)

def active():
    result = subprocess.run(['omarchy-shell', 'spacetime', 'status'], capture_output=True, text=True)
    try:
        status = json.loads(result.stdout)
        expected = json.loads((ROOT / 'plugin/manifest.json').read_text())['version']
        return result.returncode == 0 and status.get('enabled') is True and status.get('version') == expected
    except (ValueError, AttributeError):
        return False

def wait_active():
    for _ in range(20):
        if active():
            return True
        time.sleep(0.25)
    return False

def main():
    run(sys.executable, str(ROOT / 'build.py'))
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup = HOME / '.config/omarchy/backups' / ('spacetime-' + stamp)
    backup.mkdir(parents=True)
    shutil.copy2(HOME / '.config/omarchy/shell.json', backup / 'shell.json')
    target = HOME / '.config/omarchy/plugins/spacetime.background'
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.copytree(target, backup / 'spacetime.background')
    # Stage a complete directory before a single atomic rename into place.
    stage = target.with_name('.spacetime-stage-' + stamp)
    shutil.copytree(ROOT / 'plugin', stage)
    old = target.with_name('.spacetime-previous-' + stamp)
    if target.exists():
        target.rename(old)
    stage.rename(target)
    if old.exists():
        shutil.rmtree(old)
    run('omarchy-shell', 'shell', 'rescanPlugins')
    run('omarchy', 'plugin', 'enable', 'spacetime.background')
    bindir = HOME / '.local/bin'
    bindir.mkdir(parents=True, exist_ok=True)
    link = bindir / 'spacetime'
    if link.exists() or link.is_symlink():
        if link.resolve() != ROOT / 'spacetime':
            shutil.copy2(link, backup / 'spacetime-command')
        link.unlink()
    link.symlink_to(ROOT / 'spacetime')
    applications = HOME / '.local/share/applications'
    applications.mkdir(parents=True, exist_ok=True)
    for slug, name, action, icon in [
        ('spacetime-desktop', 'Spacetime Desktop', 'start', 'preferences-desktop-wallpaper'),
        ('spacetime-pause', 'Pause Spacetime Desktop', 'pause', 'media-playback-pause'),
        ('spacetime-static', 'Static Desktop Background', 'stop', 'preferences-desktop-wallpaper'),
        ('spacetime-preview', 'Spacetime Preview', 'preview', 'video-display')]:
        (applications / (slug + '.desktop')).write_text(
            '[Desktop Entry]\nType=Application\nName=' + name + '\n'
            'Exec=\"' + str(ROOT / 'spacetime').replace('\\', '\\\\').replace('\"', '\\\"').replace('`', '\\`').replace('$', '\\$') + '\" ' + action + '\n'
            'Icon=' + icon + '\nTerminal=false\nCategories=Utility;\n')
    if not wait_active():
        # The stock command refuses to restart a live secure lock session.
        print('Plugin reload retained the previous renderer; restarting the shell.')
        run('omarchy', 'restart', 'shell')
        if not wait_active():
            raise RuntimeError('Background was installed but did not activate; inspect quickshell logs.')
    run('omarchy', 'hook', 'install', 'theme-set', str(ROOT / 'hooks/80-spacetime-singularity'))
    print('Installed and verified Spacetime Desktop. Backup: ' + str(backup))

if __name__ == '__main__':
    main()
