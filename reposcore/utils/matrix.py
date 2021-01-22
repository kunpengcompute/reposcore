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


# This list contains the project which has submodules need to be count.
NEED_SUBMODULE_MAPPING = [
    'openstack/openstack',
]
