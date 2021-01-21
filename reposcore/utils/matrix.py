# This List contains the contributor name that can't be deal with json format.
AUTHOR_FIX_MAPPING = [
    ('freedom"', 'freedom'),
    ('"henyxia"', 'henyxia'),
    ('"Tempa Kyouran"', 'Tempa Kyouran'),
    ('"TBBle"', 'TBBle'),
]


# This list contains the project that `git` tool is broken.
BROKEN_PROJECT_MAPPING = [
    'openstack-tempest-skiplist',
    'whitebox-tempest-plugin',
    'xstatic-graphlib',
]


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
