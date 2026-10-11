# Puppet: declarative manifest (Puppet DSL). The agent on each node pulls a compiled
# catalog from the Puppet primary server (HTTPS 8140) every 30 min by default.
node 'web01.example.com' {
  package { 'chrony':
    ensure => installed,
  }

  file { '/etc/chrony.conf':
    ensure  => file,
    content => "server 10.0.0.1 iburst\n",
    require => Package['chrony'],
    notify  => Service['chronyd'],
  }

  service { 'chronyd':
    ensure => running,
    enable => true,
  }
}
