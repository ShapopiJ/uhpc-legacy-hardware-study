import csv, statistics as st, math
rows=list(csv.DictReader(open("timing_fixed.csv")))
def sd(x): return st.stdev(x) if len(x)>1 else 0.0
gov={}; rdma={}; cond={}
for r in rows:
    s=float(r["bench_seconds"])
    gov.setdefault(r["governor"],[]).append(s)
    rdma.setdefault(r["rdma"],[]).append(s)
    cond.setdefault(r["condition"],[]).append(s)
print("Per condition (n=4 each):")
for c in "ABCD":
    x=cond[c]; print("  {}: mean={:.1f} sd={:.1f} vals={}".format(c, st.mean(x), sd(x), [round(v) for v in x]))
o=gov["ondemand"]; p=gov["performance"]
d=st.mean(o)-st.mean(p); se=math.sqrt(st.variance(o)/len(o)+st.variance(p)/len(p)); tc=2.145
print("\nBy GOVERNOR:")
print("  ondemand:    mean={:.1f} sd={:.1f} (n={})".format(st.mean(o), sd(o), len(o)))
print("  performance: mean={:.1f} sd={:.1f} (n={})".format(st.mean(p), sd(p), len(p)))
print("  effect (performance faster) = {:.1f} s = {:.2f}%".format(d, 100*d/st.mean(o)))
print("  Welch t={:.2f}  95% CI = [{:.0f}, {:.0f}] s = [{:.2f}%, {:.2f}%]".format(
      d/se, d-tc*se, d+tc*se, 100*(d-tc*se)/st.mean(o), 100*(d+tc*se)/st.mean(o)))
a=rdma["active"]; i=rdma["inactive"]
dr=st.mean(a)-st.mean(i); ser=math.sqrt(st.variance(a)/len(a)+st.variance(i)/len(i))
print("\nBy RDMA:")
print("  active:   mean={:.1f} sd={:.1f}".format(st.mean(a), sd(a)))
print("  inactive: mean={:.1f} sd={:.1f}".format(st.mean(i), sd(i)))
print("  effect (inactive faster) = {:.1f} s = {:.2f}%  t={:.2f}".format(-dr, 100*(-dr)/st.mean(a), dr/ser))
allv=[float(r["bench_seconds"]) for r in rows]
print("\nOverall: mean={:.1f}s sd={:.1f}s min={:.1f} max={:.1f}".format(st.mean(allv), sd(allv), min(allv), max(allv)))
