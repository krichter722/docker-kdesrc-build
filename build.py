#!/usr/bin/python3

"""
Usage: build.py [options] [--] [<kdesrc-build-args>...]

Options:
    -b --base DISTRO        Use DISTRO as base system [Default: all]
    --no-cache              Do not use cache when building the image [Default: False]
    --rm                    Automatically remove the container when it exits [Default: True]
    --root                  Run kdesrc-build as root user. Useful to install files in /usr for example [Default: False]
    --display DISPLAY       Change the DISPLAY environment variable passed to the container [Default: :0]
    --xsocket PATH          Change the PATH to your X server socket dir, which will be mounted as a volume into the container [Default: /tmp/.X11-unix/]
    -h --help               Display this message

"""

from docopt import docopt
import os
import sys
import re
import subprocess

MNT_DIR = os.path.expanduser('~') + '/kdebuild'

__SCRIPT_CUR_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

def check_templates(sel_distro):
    regexp_str = ''
    avail_templates = []
    if sel_distro == 'all':
        regexp_str = '^Dockerfile-(.+)$'
    else:
        regexp_str = '^Dockerfile-({})$'.format(sel_distro)
    reg = re.compile(regexp_str)
    for i in os.listdir(__SCRIPT_CUR_DIR):
        if reg.match(i):
            avail_templates.append( reg.match(i).group(1) )
    return avail_templates


def check_mnt_point(template):
    print("Checking mount point for {}".format(template))
    path = '{}/{}'.format(MNT_DIR, template)
    os.makedirs(path, exist_ok=True)

def update_image(template, cache_enabled):
    print("Updating image for " + template)
    source = 'Dockerfile-{}'.format(template)
    dest = 'Dockerfile'
    if os.path.exists(dest):
        os.remove(dest)
    os.symlink(source, dest)
    subprocess.call(['docker',
        'build',
        '--no-cache={}'.format(str(cache_enabled)),
        '-t',
        template + '-kdedev',
        '.'
    ])

def run_kdesrc_build(template, auto_rm_enabled, run_as_root, display, xsocket_path, kdesrc_args):
    host_mnt_dir = '{}/{}'.format(MNT_DIR, template)
    sudo = ''
    if run_as_root:
        sudo = 'sudo'
    cmd = 'cd kdesrc-build && git pull && {} ./kdesrc-build '.format(sudo)
    cmd += ' '.join(kdesrc_args)
    subprocess.call(['docker',
        'run',
        '-it',
        '--rm={}'.format(str(auto_rm_enabled)),
        '-e', 'DISPLAY={}'.format(display),
        '-v', '{}:/work'.format(host_mnt_dir),
        '-v', __SCRIPT_CUR_DIR + '/kdesrc-buildrc:/home/kdedev/.kdesrc-buildrc',
        '-v', '{}:/tmp/.X11-unix/'.format(xsocket_path),
        template + '-kdedev',
        '-c',
        cmd
    ])

if __name__ == '__main__':
    args = docopt(__doc__)
    print(args)
    templates = check_templates(args['--base'])
    os.makedirs(MNT_DIR, exist_ok=True)
    for i in templates:
        print(i)
        check_mnt_point(i)
        update_image(i, args['--no-cache'])
        run_kdesrc_build(i, args['--rm'], args['--root'], args['--display'], args['--xsocket'], args['<kdesrc-build-args>'])
