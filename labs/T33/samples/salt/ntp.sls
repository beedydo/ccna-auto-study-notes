# Salt: YAML state file (SLS). The master pushes over a ZeroMQ bus (4505/4506)
# to minions (agents); salt-ssh is the agentless option.
chrony:
  pkg.installed: []

/etc/chrony.conf:
  file.managed:
    - contents: "server 10.0.0.1 iburst"
    - require:
      - pkg: chrony

chronyd:
  service.running:
    - enable: true
    - watch:
      - file: /etc/chrony.conf
