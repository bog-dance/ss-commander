#!/usr/bin/python
import git,os,json,re, shutil, subprocess, urllib2

working_dir = '/var/git/seo-sites-tc/'
git_server = '<GIT_SERVER_ADDRESS'
git_user = 'git'
git_group = 'production'
domains_list_file = working_dir + 'list2'


def get_urls():
    urls = ''
    GitServerAddress = git_server + '/api/v3/groups/seo-sites/'

    req = urllib2.Request(GitServerAddress)
    req.add_header('PRIVATE-TOKEN', '<PRIVATE_TOKEN>')
    resp = urllib2.urlopen(req)
    content = resp.read()

    parsed_json = json.loads(content)
    urls =  [i['ssh_url_to_repo'] for i in parsed_json['projects']]

    return urls

def git_clone():
    git.Repo.clone_from(url, ProjectName)
    return None


def git_apply():
    os.chdir(working_dir + ProjectName)
    repo = git.Repo.init(working_dir + ProjectName)
    repo.git.add(working_dir + ProjectName)
    repo.git.commit(m='moved builds to build and changed nginx configs')
    repo.git.push()
    print ProjectName + "push done"
    return None

def get_keys():
    order_file = working_dir + ProjectName + '/crm-proxy/wp-content/special/proxy_order.php'
    track_file = working_dir + ProjectName + '/crm-proxy/wp-content/special/proxy_track.php'

    if os.path.isfile(order_file):
        o = open(order_file, "r+")
        for line in o:
            if re.search('->setHostKey', line):
                order_key = re.findall('->setHostKey\W+([a-zA-Z0-9]+)', line)[0]
    else:
        print order_file
        report.write('could not get key in ' + order_file + '\n')

    if os.path.isfile(track_file):
        o = open(track_file, "r+")
        for line in o:
            if re.search('->setHostKey', line):
                track_key = re.findall('->setHostKey\W+([a-zA-Z0-9]+)', line)[0]
    else:
        report.write('could not get the key in ' + track_file + '\n')
        print track_file

    return order_key, track_key

def template_replacement(host_key):
    template_file = working_dir + 'template.crm-proxy.php'
    crm_proxy_path = 'crm-proxy/wp-content/special'
    crm_proxy_file = 'proxy_order.php'
    out_file = working_dir + ProjectName + '/' + crm_proxy_path + '/' + crm_proxy_file
    if os.path.isfile(out_file):
        o = open(template_file, "r+")
        data = open(template_file).read()
        o.close()
        data = data.replace('%host_key%', host_key)
        out = open(out_file, 'wt')
        out.write(data)
        out.close()
    else:
        report.write(ProjectName + '\n')

def create_crm_config():
    template_file = working_dir + 'template.crm.config.prod.php'
    crm_conf_path = working_dir + ProjectName + '/builds/configs'
    os.mkdir(crm_conf_path + '/crm-plugin')
    out_file = crm_conf_path + '/crm-plugin/' + 'config.prod.php'
    crm_conf_file = crm_conf_path + '/config.prod.php'
    o = open(template_file, "r+")
    data = open(template_file).read()
    o.close()
    data = data.replace('%orderApiKey%', keys[0]).replace('%trackApiKey%', keys[1])
    out = open(out_file, 'wt')
    out.write(data)
    out.close()

def build_scenario_modify():
    template_file = working_dir + 'template.build.prod.xml'
    o = open(template_file, "r+")
    data = open(template_file).read()
    o.close()
    out_file = working_dir + ProjectName + '/builds/build.prod.xml'
    data = data.replace('%domain_name%', domain_name )
    out = open(out_file, 'wt')
    out.write(data)
    out.close()
    return None

def git_submodules():
    os.chdir(working_dir + ProjectName)
    subprocess.check_output('git submodule add -b release <CRM_PROXY_GIT_REPO_ADRESS> crm/crm-proxy', shell = True)
    subprocess.check_output('git submodule add -b release git <CRM_PROXY_PLUGIN_GIT_REPO_ADDRESS crm/crm-proxy-plugin', shell = True)
    return None

def nginx_conf():
    template_file = working_dir + 'templates/template.nginx.prod.conf'

    nginx_settings = {
'%ProjectName%' : ProjectName,
'%HostIp%' : HostIp
}

    o = open(template_file, "r+")
    data = open(template_file).read()
    o.close()

    for key in nginx_settings:
        data = data.replace(key, nginx_settings[key])

    out_file = working_dir + ProjectName + '/build/configs/nginx/' + ProjectName +'.conf'
    out = open(out_file, 'wt')
    out.write(data)
    out.close()


def get_ip():
    NginxFile = working_dir + ProjectName + '/build/configs/nginx/' + ProjectName + '.conf'

    if os.path.isfile(NginxFile):
        o = open(NginxFile, "r+")
        for line in o:
            if re.search('listen', line):
                HostIp = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line)[0]
    else:
        print NginxFile
        report.write('could not get ip address in ' + NginxFile + '\n')

    return HostIp

def mv_build_folder():
    SrcDir = working_dir + ProjectName + '/builds'
    DstDir = working_dir + ProjectName + '/build'

    if os.path.isdir(SrcDir):
        report.write((SrcDir + '\n'))
        os.chdir(working_dir + ProjectName)
        shutil.move(SrcDir, DstDir)

    return None



report_file = working_dir + 'report'
report= open(report_file, 'wt')


urls = get_urls()
for url in urls:
    try:
        ProjectName = ((url.split('/'))[1]).split('.git')[0]
        git_apply()
    except Exception as e:
        report.write((ProjectName + str(e)))


report.close()
