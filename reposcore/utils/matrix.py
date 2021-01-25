# This list contains the project that `git` tool is broken.
BROKEN_PROJECT_MAPPING = {
    'openstack/openstack': [
        'openstack-tempest-skiplist',
        'whitebox-tempest-plugin',
        'xstatic-graphlib']
}


# TODO(yikun): language file extension map should be more complete
LANGUAGE_MAPPING = {
    "C": ['c', 'h'],
    "C++": ['cc', 'c', 'cpp', 'h', 'cxx', 'hxx'],
    "Java": ['java', 'scala'],
    "Go": ['go'],
    "Python": ['py', 'cfg'],
    "Scala": ['java', 'scala'],
}

# OpenStack core prjects.
OPENSTACK_SUBMODULE = [
    "nova",
    "neutron",
    "cinder",
    "ironic",
    "glance",
    "horizon",
    "manila",
    "keystone",
    "ceilometer",
    "neutron-lib",
    "swift",
    "heat",
    "designate",
    "trove",
    "sahara",
    "sahara-plugin-ambari",
    "sahara-plugin-spark",
    "sahara-plugin-storm",
    "sahara-plugin-cdh",
    "sahara-plugin-vanilla",
    "sahara-plugin-mapr",
]

# This list contains the project which has submodules need to be count.
SUBMODULE_MAPPING = {
    'openstack/openstack': OPENSTACK_SUBMODULE
}
