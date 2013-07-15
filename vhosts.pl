# create a new site type, which pulls the proxy branch of the repo

$sites->{citizenconnectproxy} = {
    user => 'citizenconnect',
    web_dir => 'web',
    private_git_repository => 'citizenconnect',
    private_git_ref => 'origin/proxy',
    git_user => 'anon',
    private_conf_dir => 'conf',
};


'citizenconnect-proxy.dev.mysociety.org' => {
    site => 'citizenconnectproxy',
    staging => 1,
    user => 'citizenconnect-staging',
    servers => [ 'firefly' ],
},

