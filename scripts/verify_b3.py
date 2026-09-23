import os
RES = "/home/ubuntu/Desktop/job-hunt/discovery/_sweep-2026-09-23f/results.tsv"
lines = open(RES).read().splitlines()
print("total rows:", len(lines))
for ln in lines[-4:]:
    f = ln.split("\t")
    print(len(f), "|", f[0], "|", f[1], "|", "attach=" + ("yes" if f[4] else "none"), "|", f[8])
    assert len(f) == 9, f
    assert all(x.strip() for x in (f[0], f[1], f[2], f[3], f[5], f[6], f[7], f[8])), f
print("ok")
