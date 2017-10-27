import glob
import os
out="<html><body>"
lastdir=""
for fname in glob.glob("./*/*.png"):
    fdir,ftag=os.path.split(fname)
    if not fdir==lastdir:
        lastdir=fdir
        out+="<h3>%s</h3>\n"%fdir
    out+='<img src="%s" title="%s"/>\n'%(fname,fname)
out+="</body></html>"
f=open('out.html','w')
f.write(out)
f.close()
print "DONE"