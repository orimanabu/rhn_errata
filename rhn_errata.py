#!/usr/bin/env python
# vim: set et sts=4 sw=4 ts=4 :

# Obtain RHEL errata from RHN.
# This depends on rhnapi (https://github.com/lanky/python-rhnapi).

import sys
import re
from pprint import pprint
from optparse import OptionParser, OptionValueError
import rhnapi
import rhnapi.channel
import rhnapi.errata

parser = OptionParser()
parser.add_option("--regexp", action="store", dest="regexp")
parser.add_option("--channel", action="store", dest="channel")
parser.add_option("--arch", action="store", type="string", dest="arch")
parser.add_option("--package", action="store", type="string", dest="package")
parser.add_option("--list-channel", action="store_true", dest="list_channel")
parser.add_option("--list-arch", action="store_true", dest="list_arch")
parser.add_option("--test", action="store_true", dest="test_flag")
parser.add_option("--server", action="store", type="string", dest="server")
parser.add_option("--user", action="store", type="string", dest="user")
parser.add_option("--password", action="store", type="string", dest="password")
parser.add_option("--pprint", action="store_true", dest="pprint")
parser.add_option("--print-package", action="store_true", dest="print_package")
parser.add_option("--print-topic", action="store_true", dest="print_topic")
parser.add_option("--print-description", action="store_true", dest="print_description")
parser.add_option("--print-bugzilla", action="store_true", dest="print_bugzilla")
parser.add_option("--count", action="store", type="int", dest="count")
(options, args) = parser.parse_args()

server = options.server if options.server else "rhn.redhat.com"
rhn = rhnapi.rhnSession(url=server, rhnlogin=options.user, rhnpassword=options.password)

if options.list_arch:
    clist = rhnapi.channel.listSoftwareChannels(rhn)
    clist.sort(lambda x, y: cmp(x['channel_arch'], y['channel_arch']))
    d = {}
    for c in clist:
        if c['channel_parent_label'] != '': continue
        d[c['channel_arch']] = 1
    for a in sorted(d.keys()):
        print a
    sys.exit()

if options.list_channel:
    clist = rhnapi.channel.listSoftwareChannels(rhn)
    clist.sort(lambda x, y: cmp(x['channel_label'], y['channel_label']))
    if options.pprint:
        pprint(clist)
    else:
        for c in clist:
            clabel = c['channel_label']
            if c['channel_parent_label'] != '': continue
            if options.arch and options.arch != c['channel_arch']:
                continue
            if options.regexp and not re.search(options.regexp, clabel):
                continue
            print clabel
    sys.exit()

if not options.channel:
    print "no channel specifiled."
    sys.exit()

errata_list = rhnapi.channel.listErrata(rhn, options.channel)
if options.pprint:
    pprint(errata_list)
    sys.exit()

count = 0
for erratum in errata_list:
    if options.package:
        if not re.search(options.package, erratum['errata_synopsis']):
            continue

    if options.count and count >= options.count: break
    count += 1

    print "==> %s / %s" % (erratum['errata_advisory'], erratum['errata_synopsis'])

    if options.print_package:
        packages = rhnapi.errata.listPackages(rhn, erratum['errata_advisory'])
        packages.sort(lambda x, y: cmp(x['package_file'], y['package_file']))
        for package in packages:
            if package['package_name'] != options.package: continue
            version = "%s-%s" % (package['package_version'], package['package_release'])

        print "===> package: %s-%s" % (options.package, version)

    detail = None
    if options.print_topic:
        detail = rhnapi.errata.getDetails(rhn, erratum['errata_advisory'])
        print "===> topic:"
        print detail['errata_topic'].strip()

    if options.print_description:
        if not detail:
            detail = rhnapi.errata.getDetails(rhn, erratum['errata_advisory'])
        print "===> description:"
        print detail['errata_description'].encode('utf-8')

    if options.print_bugzilla:
        print "===> related bugzilla:"
        bz_list = rhnapi.errata.bugzillaFixes(rhn, erratum['errata_advisory'])
        for bzid in sorted(bz_list.keys()):
            print "   %s\t%s" % (bzid, bz_list[bzid])

    if options.print_topic or options.print_description or options.print_bugzilla:
        print
        print


