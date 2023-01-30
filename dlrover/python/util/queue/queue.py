import queue
import threading 

class ConcurrentQueue:
    def __init__(self, capacity = -1):
        self.__capacity = capacity           
        self.__mutex = threading.Lock()      
        self.__cond  = threading.Condition(self.__mutex)     
        self.__queue = queue.Queue()    

    def get(self):
        if  self.__cond.acquire():           
            while self.__queue.empty():
                self.__cond.wait()           
            elem = self.__queue.get()
            self.__cond.notify()
            self.__cond.release()
        return elem

    def put(self, elem):
        if self.__cond.acquire():
            while self.__queue.qsize() >= self.__capacity:
                self.__cond.wait()
            self.__queue.put(elem)
            self.__cond.notify()
            self.__cond.release()

    def clear(self):
        if self.__cond.acquire():
            self.__queue.queue.clear()
            self.__cond.release()
            self.__cond.notifyAll()

    def empty(self):
        is_empty = False;
        if self.__mutex.acquire():             
            is_empty = self.__queue.empty()
            self.__mutex.release()
        return is_empty

    def size(self):
        size = 0
        if self.__mutex.acquire():
            size = self.__queue.qsize()
            self.__mutex.release()
        return size

    def resize(self,capacity = -1):
        self.__capacity = capacity
 


class RayEventQueue:
    _instance_lock = threading.Lock()
    def __init__(self):
        self.queue = ConcurrentQueue(capacity=1000)

    def put(self, value):
        return self.queue.put(value)
        
    def get(self):
        return self.queue.get()

    def size(self):
        return self.queue.size()
    
    @classmethod
    def singleton_instance(cls, *args, **kwargs):
        if not hasattr(RayEventQueue, "_instance"):
            with RayEventQueue._instance_lock:
                if not hasattr(RayEventQueue, "_instance"):
                    RayEventQueue._instance = RayEventQueue(*args, **kwargs)
        return RayEventQueue._instance
