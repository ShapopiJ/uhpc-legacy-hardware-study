#!/bin/bash
# ONE-TIME SETUP -- run this ONCE, as root, ON sp0-00.
#   ssh sp0-00
#   sudo bash /home/jshapopi/Projects/GammapyBench/setup_gammapy_sudo.sh
#
# Installs a narrow, root-owned helper that sets the CPU governor + rdma-ndd
# for one of the four 2x2 conditions, and a sudoers rule letting jshapopi run
# ONLY that helper without a password. This is the minimum privilege needed to
# drive the campaign unattended. (sp0-00 is diskless/tmpfs, so this lives until
# the node reboots -- fine for a ~1-day campaign; re-run if the node reboots.)
set -e

install -m 0755 -o root -g root /dev/stdin /usr/local/sbin/gammapy_setcond <<'EOF'
#!/bin/bash
# Set CPU governor + rdma-ndd for a Gammapy 2x2 condition. Arg: A|B|C|D
set -e
case "$1" in
  A) GOV=ondemand;    RDMA=start ;;   # baseline
  B) GOV=ondemand;    RDMA=stop  ;;
  C) GOV=performance; RDMA=start ;;
  D) GOV=performance; RDMA=stop  ;;   # fully tuned
  *) echo "usage: gammapy_setcond A|B|C|D" >&2; exit 2 ;;
esac
for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo "$GOV" > "$f"; done
systemctl "$RDMA" rdma-ndd 2>/dev/null || true
echo "condition $1 set: governor=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor) rdma-ndd=$(systemctl is-active rdma-ndd 2>&1)"
EOF

echo 'jshapopi ALL=(root) NOPASSWD: /usr/local/sbin/gammapy_setcond' > /etc/sudoers.d/gammapy_campaign
chmod 0440 /etc/sudoers.d/gammapy_campaign
visudo -c
echo "=== setup OK. Test as jshapopi: ssh sp0-00 'sudo -n /usr/local/sbin/gammapy_setcond D' ==="
