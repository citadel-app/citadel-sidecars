import docker
import time
import os
import threading
from typing import Dict, List, Optional
import queue

class ContainerManager:
    def __init__(self):
        self.client = docker.from_env()
        self.idle_pools: Dict[str, queue.Queue] = {}
        self.lock = threading.Lock()
        
        # Configuration
        self.pool_size = 2 # Keep 2 idle containers per image
        self.supported_images = [
            "python:3.9-slim",
            "node:18-alpine"
        ]

    def warm_up_pools(self):
        """Starts background thread to maintain pools"""
        threading.Thread(target=self._maintain_pools, daemon=True).start()

    def _maintain_pools(self):
        while True:
            for image in self.supported_images:
                if image not in self.idle_pools:
                    self.idle_pools[image] = queue.Queue()
                
                current_pool = self.idle_pools[image]
                if current_pool.qsize() < self.pool_size:
                    try:
                        print(f"[ContainerManager] Warming up {image}...")
                        container = self.client.containers.run(
                            image, 
                            "tail -f /dev/null", # Keep alive
                            detach=True,
                            mem_limit="128m",
                            cpu_quota=50000, # 50% CPU
                            network_mode="none", # Isolation
                            labels={
                                "managed-by": "codex",
                                "role": "execution-pool",
                                "pool-image": image
                            }
                        )
                        current_pool.put(container)
                    except Exception as e:
                        print(f"[ContainerManager] Failed to warm up {image}: {e}")
            
            time.sleep(5)

    def get_container(self, image: str):
        """Gets a warm container or creates new one"""
        if image in self.idle_pools and not self.idle_pools[image].empty():
            try:
                container = self.idle_pools[image].get_nowait()
                # Verify it's still running
                container.reload()
                if container.status == 'running':
                    print(f"[ContainerManager] Setup: Using warm container {container.short_id}")
                    return container, True # True = is_warm
                else:
                    container.remove(force=True)
            except:
                pass
        
        # Fallback: create fresh
        print(f"[ContainerManager] No warm container for {image}, starting fresh...")
        container = self.client.containers.run(
            image, 
            "tail -f /dev/null",
            detach=True,
            mem_limit="128m",
            network_mode="none",
            labels={
                "managed-by": "codex",
                "role": "execution-pool",
                "pool-image": image
            }
        )
        return container, False

    def purge_pool(self):
        """Kills all containers in the idle pool and any orphans with the matching label"""
        print("[ContainerManager] Purging all pool containers...")
        # 1. Clear known idle containers in queues
        for image in self.idle_pools:
            q = self.idle_pools[image]
            while not q.empty():
                try:
                    container = q.get_nowait()
                    container.remove(force=True)
                except:
                    pass
        
        # 2. Safety: kill any remaining containers with our labels
        try:
            orphans = self.client.containers.list(
                all=True, 
                filters={"label": ["managed-by=codex", "role=execution-pool"]}
            )
            for container in orphans:
                try:
                    print(f"[ContainerManager] Removing orphan pool container: {container.short_id}")
                    container.remove(force=True)
                except:
                    pass
        except Exception as e:
            print(f"Error purging orphans: {e}")

    def cleanup(self, container, is_warm: bool):
        """
        If it was a warm container, we might want to kill it to clear state 
        (since we can't easily reset filesystem/memory state perfectly).
        For now, ALWAYS kill used containers to ensure isolation.
        The pool manager will replace it.
        """
        try:
            container.remove(force=True)
        except Exception as e:
            print(f"Error cleaning up container: {e}")
