#!/usr/bin/python

class Prefix(object):
    def __init__(self, pfx):
        self.set_prefix(pfx)
    def clear(self):
        self.origin_as = {}
    def set_prefix(self, pfx):
        self.pfx = pfx
        self.clear()
    def set_origin(self, asn, announced_by):
        self.origin_as[asn] = announced_by
    def is_consistent(self):
        return len(self.origin_as)==1
    def __str__(self):
        s = self.pfx+" "
        if self.is_consistent:
            return s+self.origin_as.keys()[0]
        else:
            return s+"I="+str(self.origin_as)

current_pfx=Prefix(None)

while True:
    try:
        mrt_line = raw_input()
    except EOFError:
        break
    flds = mrt_line.split("|")
    (header,tstamp,b,peer,peer_as,pfx,aspath,learnt,next_hop,lcl_pref,med,cty,ag_flag,ag,junk) = mrt_line.split("|")
    if header != "TABLE_DUMP2":
        continue
    if pfx != current_pfx.pfx:
        if current_pfx.pfx:
            print str(current_pfx)
        current_pfx.set_prefix(pfx)
    origin=aspath.split(" ")[-1]
    current_pfx.set_origin(origin,peer_as)
    #print tstamp,pfx,aspath

print str(current_pfx)
