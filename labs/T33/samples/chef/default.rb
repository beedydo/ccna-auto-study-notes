# Chef: a recipe (Ruby DSL) inside a cookbook. Chef Infra Client on each node
# periodically contacts Chef Infra Server, fetches cookbooks and converges.
package 'chrony'

file '/etc/chrony.conf' do
  content "server 10.0.0.1 iburst\n"
  notifies :restart, 'service[chronyd]'
end

service 'chronyd' do
  action [:enable, :start]
end
