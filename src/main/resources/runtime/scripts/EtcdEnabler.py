import os
import time
import sys
import os.path
import stat
import re
from subprocess import call

from com.datasynapse.fabric.util import ContainerUtils
from com.datasynapse.fabric.common import RuntimeContextVariable
from com.datasynapse.fabric.common import ActivationInfo


class EtcdMember:
    
    def __init__(self, additionalVariables):
        " initialize etcd cluster member"
        
        self.__clusterConfigDir = getVariableValue("CLUSTER_CONFIG_DIR")
        
        if not self.__clusterConfigDir:
                raise "CLUSTER_CONFIG_DIR is required"
        
        componentName = proxy.container.currentDomain.name
        self.__clusterConfigDir = os.path.join(self.__clusterConfigDir, componentName)
        
        self.__workDir = getVariableValue("CONTAINER_WORK_DIR")
        
        name = getVariableValue("NAME_PREFIX", "default")
        self.__etcdName = name + getVariableValue("LISTEN_ADDRESS") + "-" + getVariableValue("ENGINE_INSTANCE")
        additionalVariables.add(RuntimeContextVariable("ETCD_NAME", self.__etcdName, RuntimeContextVariable.ENVIRONMENT_TYPE, "Etcd member name", False, RuntimeContextVariable.NO_INCREMENT))
     
        self.__lockExpire = int(getVariableValue("LOCK_EXPIRE", "300000"))
        self.__lockWait = int(getVariableValue("LOCK_WAIT", "30000"))
        self.__staleWait = int(getVariableValue("STALE_CONFIG_WAIT", "300"))
        
        self.__memberId = None
        
        changePermissions(os.path.join(self.__workDir, "etcd"))
        self.__clientConfig = getVariableValue("ETCD_ADVERTISE_CLIENT_URLS")
        
        self.__lock()
        self.__etcdCluster = self.__getEtcdCluster()
        members = self.__getMemberList()
            
        if (members):
            if self.__memberId:
                self.__updateMember()
            else:
                self.__addMember()
            additionalVariables.add(RuntimeContextVariable("ETCD_INITIAL_CLUSTER_STATE", "existing", RuntimeContextVariable.ENVIRONMENT_TYPE, "Etcd initial cluster state", False, RuntimeContextVariable.NO_INCREMENT))
        else:
            additionalVariables.add(RuntimeContextVariable("ETCD_INITIAL_CLUSTER_STATE", "new", RuntimeContextVariable.ENVIRONMENT_TYPE, "Etcd initial cluster state", False, RuntimeContextVariable.NO_INCREMENT))
       
        etcdInitialCluster = self.__getInitialCluster(members)
        additionalVariables.add(RuntimeContextVariable("ETCD_INITIAL_CLUSTER", etcdInitialCluster, RuntimeContextVariable.ENVIRONMENT_TYPE, "Etcd initial cluster", False, RuntimeContextVariable.NO_INCREMENT))
        etcdUrls="etcd://"+str(self.__etcdCluster).replace("http://", "")
        additionalVariables.add(RuntimeContextVariable("ETCD_ADDRESS", etcdUrls, RuntimeContextVariable.ENVIRONMENT_TYPE, "Etcd address", True, RuntimeContextVariable.NO_INCREMENT))
    
    def __getInitialCluster(self, members):
        etcdInitialCluster = None
        
        if not self.__memberId:
            etcdInitialCluster = self.__etcdName + "=" + getVariableValue("ETCD_INITIAL_ADVERTISE_PEER_URLS")
        
        if members:
            for member in members:
                str = None
                try:
                    str = member["name"] +"=" + member["peerURLs"]
                except:
                    str = None
                    type, value, traceback = sys.exc_info()
                    logger.severe("member key error:" + `value`)
            
                if str:
                    if etcdInitialCluster:
                        etcdInitialCluster = etcdInitialCluster +"," + str
                    else:
                        etcdInitialCluster = str
                
        return etcdInitialCluster
            
    def __addMember(self):
        try:
            cmd = os.path.join(self.__workDir, "etcd", "etcdctl")
            cmdlist = [cmd, "--endpoint", self.__etcdCluster, "member", "add", self.__etcdName, getVariableValue("ETCD_INITIAL_ADVERTISE_PEER_URLS")]
            logger.info("Executing:" + list2str(cmdlist))
            retcode = call(cmdlist)
            logger.info("Return code:" + `retcode`)
        except:
            type, value, traceback = sys.exc_info()
            logger.severe("add member error:" + `value`)
       
    def __updateMember(self):
        try:
            if self.__memberId:
                cmd = os.path.join(self.__workDir, "etcd", "etcdctl")
                cmdlist = [cmd, "--endpoint", self.__etcdCluster, "member", "update", self.__memberId, getVariableValue("ETCD_INITIAL_ADVERTISE_PEER_URLS")]
                logger.info("Executing:" + list2str(cmdlist))
                retcode = call(cmdlist)
                logger.info("Return code:" + `retcode`)
        except:
            type, value, traceback = sys.exc_info()
            logger.severe("add member error:" + `value`)
            
    def __removeMember(self):
        try:
            if self.__memberId:
                cmd = os.path.join(self.__workDir, "etcd", "etcdctl")
                cmdlist = [cmd, "--endpoint", self.__etcdCluster, "member", "remove", self.__memberId]
                logger.info("Executing:" + list2str(cmdlist))
                retcode = call(cmdlist)
                logger.info("Return code:" + `retcode`)
        except:
            type, value, traceback = sys.exc_info()
            logger.severe("remove member error:" + `value`)
      
    
    def __getMemberList(self):
        file = None
        members = []
        
        try:
            path = os.path.join(self.__workDir, "etcdctl.out")
            file = open(path, "w")
        
            cmd = os.path.join(self.__workDir, "etcd", "etcdctl")
            cmdlist = [cmd, "--endpoint", self.__etcdCluster, "member", "list"]
            logger.info("Executing:" + list2str(cmdlist))
            retcode = call(cmdlist, stdout=file)
            logger.info("Return code:" + `retcode`)
            file.close()
            
            if retcode == 0:
                file = open(path, "r")
                lines = file.readlines()
                for line in lines:
                    list = line.split()
                    member = {}
                    for item in list[1:]:
                        kv = item.split("=")
                        member[kv[0]] = kv[1]
                        if kv[0] == "name" and kv[1] == self.__etcdName:
                            self.__memberId = str(list[0]).strip(":")
                            
                    members.append(member)
                logger.info("Cluster members:" + str(members))
        except:
            type, value, traceback = sys.exc_info()
            logger.severe("get running cluster error:" + `value`)
        finally:
            if file:
                file.close()
                
        return members
        
    def __readConfig(self, path):
        "read server id information from file"
        file = None
        config = None
        try:
            if os.path.isfile(path):
                file = open(path, "r")
                lines = file.readlines()
                for line in lines:
                    config = line.strip()
                    break;
        finally:
            if file:
                file.close()
                
        return config
    
    def __writeConfig(self, path, config):
        "write  config"
        
        file = None
        try:
            file = open(path, "w")
            file.write(config + "\n")
        finally:
            if file:
                file.close()
                
    def __getEtcdCluster(self):
        "get etcd cluster address"
        
        etcdCluster = self.__clientConfig
                
        list = os.listdir(self.__clusterConfigDir)
        for name in list:
            path = os.path.join(self.__clusterConfigDir, name)
                
            if name[:7] == "client.":
                if time.time() - os.path.getmtime(path) > self.__staleWait:
                    logger.info("Removing stale client configuration file:" + path)
                    os.remove(path)
                else:
                    logger.info('Reading client configuration:' + path)
                    clientConfig = self.__readConfig(path)
                    
                    if clientConfig:
                        etcdCluster = etcdCluster + "," + clientConfig
                     
            
        return etcdCluster
        
    def __lock(self):
        "get global lock"
        self.__locked = ContainerUtils.acquireGlobalLock(self.__clusterConfigDir, self.__lockExpire, self.__lockWait)
        if not self.__locked:
            raise "Unable to acquire global lock:" + self.__clusterConfigDir
    
    def __unlock(self):
        "unlock global lock"
        if self.__locked:
            ContainerUtils.releaseGlobalLock(self.__clusterConfigDir)
            self.__locked = None
            
    def isNodeRunning(self):
        " is node running"
        
        path = os.path.join(self.__clusterConfigDir, "client." + self.__etcdName)
        self.__writeConfig(path, self.__clientConfig)
        return True
                    
    def hasNodeStarted(self):
        " has node started"
        started=False
        self.__memberId = None
        self.__getMemberList()
        if self.__memberId:
            path = os.path.join(self.__clusterConfigDir, "client." + self.__etcdName)
            self.__writeConfig(path, self.__clientConfig)
            started = True
            self.__unlock()
            logger.info("Cluster member started:" + self.__memberId)
            
        return started

    def __cleanup(self):
        try:
            path = os.path.join(self.__clusterConfigDir, "client." + self.__etcdName)
            if os.path.isfile(path):
                os.remove(path)
        except:
            type, value, traceback = sys.exc_info()
            logger.severe("cleanup files error:" + `value`)
        finally:
             self.__unlock()
            
    def shutdownNode(self):
        "shutdown node"
        self.__removeMember()
        self.__cleanup()
        proxy.doShutdown()
            

def list2str(list):
    content = str(list).strip('[]')
    content = content.replace(",", " ")
    content = content.replace("u'", "")
    content = content.replace("'", "")
    return content

def mkdir_p(path, mode=0700):
    if not os.path.isdir(path):
        logger.info("Creating directory:" + path)
        os.makedirs(path, mode)
    
def changePermissions(dir):
    logger.info("chmod:" + dir)
    os.chmod(dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
      
    for dirpath, dirnames, filenames in os.walk(dir):
        for dirname in dirnames:
            dpath = os.path.join(dirpath, dirname)
            os.chmod(dpath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
           
        for filename in filenames:
               filePath = os.path.join(dirpath, filename)
               os.chmod(filePath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                
def copyContainerEnvironment():
    count = runtimeContext.variableCount
    for i in range(0, count, 1):
        rtv = runtimeContext.getVariable(i)
        if rtv.type == "Environment":
            os.environ[rtv.name] = rtv.value
    
    os.unsetenv("LD_LIBRARY_PATH")
    os.unsetenv("LD_PRELOAD")
              
def getVariableValue(name, value=None):
    "get runtime variable value"
    var = runtimeContext.getVariable(name)
    if var != None:
        value = var.value
    
    return value

def doInit(additionalVariables):
    "do init"
    etcdNode = EtcdMember(additionalVariables)
    etcdNodeRcv = RuntimeContextVariable("ETCD_MEMBER_OBJECT", etcdNode, RuntimeContextVariable.OBJECT_TYPE)
    runtimeContext.addVariable(etcdNodeRcv)

def doShutdown():
    "do shutdown"
    logger.info("Enter EtcdEnabler:doShutdown")
    try:
        etcdNode = getVariableValue("ETCD_MEMBER_OBJECT")
        if etcdNode:
            etcdNode.shutdownNode()
    except:
        type, value, traceback = sys.exc_info()
        logger.severe("EtcdEnabler:doShutdown:JMX Shutdown error:" + `value`)
    
    logger.info("Exit EtcdEnabler:doShutdown")

def hasContainerStarted():
    logger.info("Enter EtcdEnabler:hasContainerStarted")
    started = False
    try:
        etcdNode = getVariableValue("ETCD_MEMBER_OBJECT")
        
        if etcdNode:
            started = etcdNode.hasNodeStarted()
            
    except:
        type, value, traceback = sys.exc_info()
        logger.severe("Unexpected error in EtcdEnabler:hasContainerStarted:" + `value`)
    logger.info("Exit EtcdEnabler:hasContainerStarted")
    return started
    
def isContainerRunning():
    running = False
    try:
        etcdNode = getVariableValue("ETCD_MEMBER_OBJECT")
        if etcdNode:
            running = etcdNode.isNodeRunning()
    except:
        type, value, traceback = sys.exc_info()
        logger.severe("Unexpected error in EtcdEnabler:isContainerRunning:" + `value`)
    
    return running

def getContainerStartConditionPollPeriod():
    poll = getVariableValue("START_POLL_PERIOD", "10000")
    return int(poll)
    
def getContainerRunningConditionPollPeriod():
    poll = getVariableValue("RUNNING_POLL_PERIOD", "60000")
    return int(poll)

