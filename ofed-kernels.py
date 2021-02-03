#!/usr/bin/env python3
""" Scan Mellanox repos for OFED vs kernel version information

    Usage:
        ./ofed-kernels.py OUTFILE
    
    Produces a json file at OUTFILE as a list of dicts with items:
    - ofed_ver: ofed_ver,
    - kernel_ver: kernel_ver
    - repo_url: URL to relevant `.repo` file
"""
import urllib.request, re, subprocess, json, sys

BASE_URL = 'https://linux.mellanox.com/public/repo/mlnx_ofed/'
URL_CHARACTER_SET = "\w\-.~:\/?#[\]@!$&'()*+ ,;%="
ARCH = 'x86_64'
OS_NAME = 'rhel'


def get_links(url):
    resource = urllib.request.urlopen(url)
    content =  resource.read().decode(resource.headers.get_content_charset())
    matches = re.findall(r'<a href=\"([%s]+)\">' % URL_CHARACTER_SET, content)
    return matches

def scan(url, os_name, arch, outfile):
    data = [] # items with be {'ofed_ver':str, 'kernel_ver':str, 'repo_url':str} or None for last two
    for link in get_links(url):
        if re.match(r'\d\.\d', link): # get links like `4.5-1.0.1.0/`
            ofed_ver = link.rstrip('/')
            for os_link in get_links(url + link):
                if os_link.startswith(os_name):
                    repo_url = url + link + os_link
                    try:
                        pkg_urls = get_links(repo_url + arch)
                    except urllib.error.HTTPError:
                        print('could not read %s' % repo_url + arch)
                        continue
                    ofa_kernel_kmod_pkg = repo_url + arch + '/' + [p for p in pkg_urls if p.startswith('kmod-mlnx-ofa_kernel')][0]
                    rpm = subprocess.run(['rpm', '-qlp', ofa_kernel_kmod_pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, universal_newlines=True)
                    kernel_ver = None
                    for line in rpm.stdout.splitlines():
                        if line.startswith('/lib/modules'): # e.g. /lib/modules/2.6.32-220.el6.x86_64/extra/mlnx-ofa_kernel
                            kernel_ver = line.split('/')[3]
                            break
                    print('processed', ofed_ver, kernel_ver, repo_url)
                    data.append({'ofed_ver':ofed_ver, 'kernel_ver':kernel_ver, 'repo_url': repo_url + 'mellanox_mlnx_ofed.repo'})
    with open(outfile, 'w') as of:
        json.dump(data, of, sort_keys=Truye, indent=4)
    print('written', outfile)

if __name__ == '__main__':
    scan(BASE_URL, OS_NAME, ARCH, sys.argv[1])