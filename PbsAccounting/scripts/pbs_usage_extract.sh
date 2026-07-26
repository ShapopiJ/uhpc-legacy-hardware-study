#!/bin/bash
# ONE-TIME -- run ONCE, as root, on the uhpc manager node:
#   sudo bash /home/jshapopi/pbs_usage_extract.sh
# Parses PBS accounting logs and writes an ANONYMIZED usage summary to
# /home/jshapopi/pbs_usage/ (users are reduced to counts, no names/commands).
set -e
ACCT=/var/spool/pbs/server_priv/accounting
OUT=/home/jshapopi/pbs_usage
mkdir -p "$OUT"

# Per-job facts from every 'E' (job-end) record, across all years.
# PBS record: MM/DD/YYYY HH:MM:SS;E;jobid;key=value key=value ...
awk -F';' '
  $2=="E" {
    split($1,d," "); split(d[1],md,"/"); year=md[3];
    line=$4;
    user=""; ncpus=""; wall=""; qtime=""; start="";
    n=split(line,kv," ");
    for(i=1;i<=n;i++){
      split(kv[i],p,"=");
      if(p[1]=="user") user=p[2];
      else if(p[1]=="Resource_List.ncpus") ncpus=p[2];
      else if(p[1]=="resources_used.walltime") wall=p[2];
      else if(p[1]=="qtime") qtime=p[2];
      else if(p[1]=="start") start=p[2];
    }
    # walltime HH:MM:SS -> seconds
    ws=0; if(wall!=""){split(wall,t,":"); ws=t[1]*3600+t[2]*60+t[3];}
    if(ncpus=="") ncpus=1;
    qwait=(start!="" && qtime!="")? start-qtime : "";
    ch=ncpus*ws/3600.0;
    jobs[year]++; corehours[year]+=ch; ublob[year]=ublob[year] user "\n";
    if(qwait!=""){qw[year]+=qwait; qn[year]++}
    seen[user]=1;
  }
  END{
    print "year,jobs,distinct_users,core_hours,mean_queue_wait_s" > "/home/jshapopi/pbs_usage/per_year.csv";
    for(y in jobs){
      # distinct users this year
      nu=split(ublob[y],arr,"\n"); delete uu; c=0;
      for(i=1;i<=nu;i++){ if(arr[i]!="" && !(arr[i] in uu)){uu[arr[i]]=1; c++} }
      mqw=(qn[y]>0)? qw[y]/qn[y] : 0;
      printf "%s,%d,%d,%.1f,%.0f\n", y, jobs[y], c, corehours[y], mqw >> "/home/jshapopi/pbs_usage/per_year.csv";
    }
    tot=0; for(u in seen) tot++;
    print "distinct_users_all_time," tot > "/home/jshapopi/pbs_usage/overall.csv";
  }
' "$ACCT"/* 2>/dev/null

sort -t, -k1 "$OUT/per_year.csv" -o "$OUT/per_year.csv"
chown -R jshapopi:jshapopi "$OUT"
echo "=== per_year.csv ==="; cat "$OUT/per_year.csv"
echo "=== overall ==="; cat "$OUT/overall.csv"
echo "=== wrote $OUT (owned by jshapopi) ==="
