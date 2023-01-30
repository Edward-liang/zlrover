
import threading
import ray 
from dlrover.python.scheduler.job import ElasticJob, JobArgs, NodeArgs
import os 
from dlrover.python.common.node import NodeGroupResource, NodeResource
from dlrover.python.master.stats.stats_backend import LocalFileStateBackend
from dlrover.python.util.state.store_mananger import StoreManager


def parse_bool(s: str):
    return s.lower() in ["true", "yes", "t", "y"]


 


@ray.remote
class RayWorker:  # pragma: no cover
    def __init__(self):
        pass 
    def exec_module(self):
        pass 
    def get_actor_address_and_port(self):
        return None


class RayClient(object):
    _instance_lock = threading.Lock()

    def __init__(self, namespace, jobname):
        self.store_manager = StoreManager(jobname=jobname, namespace=namespace).build_store_manager()
        self.store = self.store_manager.build_store()

    def create_pg(self, resource):
        pass 

    def create_actor(self, actor_args):
        # 反射方法获取worker
        executor = actor_args.get("executor") 
        args = actor_args.get("args", [])
        kwargs = actor_args.get("kargs", {})
        actor_name = actor_args.get("actor_name", "actor")
        actor_handle = ray.remote(executor).options(name=actor_name).remote(*args,**kwargs)
        self.store.add_actor_name(actor_name)
        return actor_handle
        
    def delete_actor(self, actor_name):
        actor_handle = self.get_actor_handle(actor_name)
        if actor_handle is None:
            print("actor exited before killing")
        else:
            ray.kill(actor_handle, no_restart=True)
        self.store.remove_actor_name(actor_name)
        return 

    def list_actor(self):
        actor_names = self.store.get("actor_names",[])
        for n in actor_names:
            status = self.check_health_status(n)
            yield n, status 
    
    def get_actor_status(self, actor_name):
        '''
           check actor status from ray dashboard
        '''
        return "RUNNING"
    
    def remote_call_actor(self, actor_handle, func, args, kargs):
        res = ray.get(getattr(actor_handle, func).remote(args,kargs))
        return res

    def check_health_status(self, actor_name):
        '''
           When Actor is in RUNNING Status, check whether estimator is initiated 
        '''
        # to do 
        # 使用dlrover python的
        status = None
        actor_handle = self.get_actor_handle(actor_name)
        if actor_handle is None:
            status = "not exist"
        res = self.remote_call_actor(actor_handle,"health_check",[],{})
        if res is not None:
            status = "RUNNING"
        else:
            status = "FAILED"
        return "RUNNING"

    def get_actor_handle(self, actor_name):
        actor_handle = None
        try:
            actor_handle = ray.get_actor(actor_name)
        except Exception as e:
            print(e) # to do: print -> logging
        return actor_handle
 
    @classmethod
    def singleton_instance(cls, *args, **kwargs):
        if not hasattr(RayClient, "_instance"):
            with RayClient._instance_lock:
                if not hasattr(RayClient, "_instance"):
                    RayClient._instance = RayClient(*args, **kwargs)
        return RayClient._instance
   

class RayElasticJob(ElasticJob):
    def __init__(self, job_name, namespace):
        """
        ElasticJob manages Pods by K8s Python APIs. The example of an elastic
        job is in dlrover/go/elasticjob_operator/config/samples/
        elastic_v1alpha1_elasticjob.yaml
        Args:
            image_name: Docker image path for ElasticDL pod.
            namespace: The name of the Kubernetes namespace where ElasticDL
                pods will be created.
            job_name: ElasticDL job name, should be unique in the namespace.
                Used as pod name prefix and value for "elastic" label.
        """
        self._ray_client = RayClient.singleton_instance(namespace, job_name)
        self._namespace = namespace
        self._job_name = job_name

    def get_node_name(self, type, id):
        return "pod-name"
    
 


class RayJobArgs(JobArgs):
    def __init__(self, platform, namespace, job_name):
        super(RayJobArgs, self).__init__(platform, namespace, job_name)
        self.file_path =   "{}.json".format(job_name)
        self.stats_backend = LocalFileStateBackend(self.file_path)
    def initilize(self):
        job = self.stats_backend.load()
        for replica, spec in job["spec"]["replicaSpecs"].items():
            num = int(spec.get("replicas", 0))
            requests = spec.get("resources", {})
            cpu = NodeResource.convert_cpu_to_decimal(requests.get("cpu", 0))
            if "memory" in requests:
                memory = NodeResource.convert_memory_to_mb(requests["memory"])
            else:
                memory = 0
            gpu_type = None
            gpu_num = 0
            for k, v in requests.items():
                if "nvidia.com" in k:
                    gpu_type = k
                    gpu_num = int(v)
            group_resource = NodeGroupResource(
                num,
                NodeResource(cpu, memory, gpu_type, gpu_num),
            )
            restart_count = int(spec.get("restartCount", 3))
            auto_scale = parse_bool(spec.get("autoScale", "True"))
            restart_timeout = int(spec.get("restartTimeout", 0))
            critical_nodes = spec.get("criticalNodes", "")
            self.node_args[replica] = NodeArgs(
                group_resource,
                auto_scale,
                restart_count,
                restart_timeout,
                critical_nodes,
            )
