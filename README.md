### etcd Enabler User Guide

### Introduction
--------------------------------------
`etcd Enabler` is used with `TIBCO Silver Fabric` to manage etcd key store cluster. This enabler was developed and tested with etcd version 2.2.5.

This Enabler supports etcd clustering. This enabler automatically configures an etcd cluster using a shared configuration directory. 
For reasons specific to etcd design, etcd cluster size should always be an odd size, 3 or larger. See [etcd] for details about etcd.

### Building the Enabler and Distribution
---------------------------------------------------
This enabler project builds a `Silver Fabric Enabler Grid Library`. It also optionally builds a `Silver Fabric Distribution Grid Library` for etcd database. 
The Silver Fabric Grid Libraries can be built by executing Maven `install`. After a successful build, the Enabler and Distribution Grid Library files 
can be found under project `target` folder. 

To build both the Enabler and Distribution Grid Libraries:

* Download etcd release tar file for 64 bit linux from `https://github.com/coreos/etcd/releases/`. For example,  download v2.2.5 `etcd-v2.2.5-linux-amd64.tar.gz` to /tmp.
* Run Maven `install` target with Java system property `distribution.location` pointing to the location of down loaded compressed tar file. For example, `-Ddistribution.location=/tmp/etcd-v2.2.5-linux-amd64.tar.gz`

If you want to build the Enabler Grid LIbrary without building Distribution Grid Library:

* Run Maven `install` target without defining `distribution.location` Java system property

### Installing the Enabler and Distribution
----------------------------------------------------
Installation of the etcd Enabler and Distribution is done by copying the etcd Enabler and Distribution Grid Libraries from the `target` project folder to the 
`SF_HOME/webapps/livecluster/deploy/resources/gridlib` folder on the Silver Fabric Broker. 

### Enabler Features
-------------------------------------------
This Enabler supports following Silver Fabric Features:

* Application Logging Support

### Enabler Statistics
-------------------------------------
This enabler supports no statistics.

### Runtime Context Variables
---------------------------------------
Silver Fabric Components using this enabler can configure following Enabler Runtime Context variables. 

### Runtime Context Variable List:
------------------------------------------

|Variable Name|Default Value|Type|Description|Export|Auto Increment|
|---|---|---|---|---|---|
|`CLUSTER_CONFIG_DIR`||String| etcd initial cluster configuration shared directory. This is the only variable that is required. .|false|None|
|`NAME_PREFIX`|default|String| Human-readable name prefix for this member.|false|None|
|`ETCD_DATA_DIR`|${CONTAINER_WORK_DIR}/${ETCD_NAME}.etcd|String| Path to the etcd data directory. Default value is non-persistent across restart.|false|None|
|`ETCD_WAL_DIR`||Environment| Path to the dedicated etcd wal directory.|false|None|
|`ETCD_SNAPSHOT_COUNT`|10000|Environment| Number of committed transactions to trigger a snapshot to disk.|false|None|
|`ETCD_HEARTBEAT_INTERVAL`|100|Environment| Time (in milliseconds) of a heart beat interval.|false|None|
|`ETCD_ELECTION_TIMEOUT`|1000|Environment| Time (in milliseconds) for an election to timeout.|false|None|
|`LISTEN_PEER_PORT`|7001|String| etcd listen peer port.|false|Numeric|
|`ETCD_LISTEN_PEER_URLS`|http://${LISTEN_ADDRESS}:${LISTEN_PEER_PORT}|Environment|etcd listen peer urls.|false|None|
|`LISTEN_CLIENT_PORT`|4001|String|etcd listen client port.|false|Numeric|
|`ETCD_LISTEN_CLIENT_URLS`|http://${LISTEN_ADDRESS}:${LISTEN_CLIENT_PORT}|Environment|etcd listen client urls.|false|None|
|`ETCD_MAX_SNAPSHOTS`|5|Environment|Maximum number of snapshot files to retain (0 is unlimited).|false|None|
|`ETCD_MAX_WALS`|5|Environment|Maximum number of WAL files to retain (0 is unlimited).|false|None|
|`ETCD_CORS`||Environment|Comma-separated white list of origins for CORS (cross-origin resource sharing).|false|None|
|`INITIAL_ADVERTISE_PEER_PORT`|7001|String|etcd listen peer port.|false|Numeric|
|`ETCD_LISTEN_CLIENT_URLS`|http://${LISTEN_ADDRESS}:${INITIAL_ADVERTISE_PEER_PORT}|Environment|etcd initial advertise peer urls.|false|None|
|`ETCD_INITIAL_CLUSTER_TOKEN`|${container.getCurrentDomain().getName()}|Environment|etcd initial cluster token for the etcd cluster during bootstrap..|false|None|
|`ADVERTISE_CLIENT_PORT`|4001|String|etcd advertise listen client port.|false|Numeric|
|`ETCD_ADVERTISE_CLIENT_URLS`|http://${LISTEN_ADDRESS}:${ADVERTISE_CLIENT_PORT}|Environment|etcd listen client urls.|true|None|
|`ETCD_STRICT_RECONFIG_CHECK`|true|Environment|Reject reconfiguration requests that would cause quorum loss.|false|None|
|`ETCD_CERT_FILE`||Environment|Path to the client server TLS certificate file.|false|None|
|`ETCD_KEY_FILE`||Environment|Path to the client server TLS key file.|false|None|
|`ETCD_CLIENT_CERT_AUTH`|false|Environment|Path to the client server TLS key file.|false|None|
|`ETCD_TRUSTED_CA_FILE`||Environment|Path to the client server TLS trusted CA key file.|false|None|
|`ETCD_PEER_CERT_FILE`||Environment|Path to the peer server TLS certificate file.|false|None|
|`ETCD_PEER_KEY_FILE`||Environment|Path to the peer server TLS key file.|false|None|
|`ETCD_PEER_CLIENT_CERT_AUTH`|false|Environment|Enable peer client certificate authentication.|false|None|
|`ETCD_PEER_TRUSTED_CA_FILE`||Environment|Path to the peer server TLS trusted CA file.|false|None|
|`ETCD_DEBUG`|false|Environment|Drop the default log level to DEBUG for all sub packages.|false|None|
|`ETCD_LOG_PACKAGE_LEVELS`|false|Environment|Set individual etcd sub packages to specific log levels. An example being etcdserver=WARNING,security=DEBUG.|false|None|

Following variables are automatically defined and exported by the Enabler :

* `ETCD_ADDRESS` This is the etcd  cluster address containing one or more cluster nodes. The format is etcd://<host:port>,...

### Component and Stack Examples
-----------------------------------------------
Below is a screenshot image from an example etcd cluster Component defined in Silver Fabric. 

* [etcd Cluster Component] (images/etcd-cluster-component.png)

Below is a screenshot image from an example etcd cluster Stack defined in Silver Fabric. 
This example defines a cluster of size 1. The cluster size is specified in the Stack. 

It is best to run no more than one etcd node on a single host. This is configured in the Component and the Stack. In the Component it is 
configured by specifying `Maximum Instances Per Host` option and in the Stack this is specified using a resource preference
rule for a specific Silver Fabric Engine Instance, for example, 0.

* [etcd Cluster Stack] (images/etcd-cluster-stack.png)

[etcd]:<https://github.com/coreos/etcd> 