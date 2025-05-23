# Copyright 2023 The DLRover Authors. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from dlrover.python.common.constants import NodeStatus, NodeType
from dlrover.python.master.elastic_training.sync_service import SyncService
from dlrover.python.master.monitor.perf_monitor import PerfMonitor
from dlrover.python.master.node.dist_job_manager import create_job_manager
from dlrover.python.master.node.job_context import get_job_context
from dlrover.python.tests.test_utils import MockK8sPSJobArgs, mock_k8s_client


class SyncServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        mock_k8s_client()
        params = MockK8sPSJobArgs()
        params.node_args
        params.initilize()
        self.job_manager = create_job_manager(params, PerfMonitor())
        self.job_manager._init_nodes()
        self.job_context = get_job_context()

    def tearDown(self):
        self.job_context.clear_job_nodes()

    def test_sync(self):
        sync_service = SyncService(self.job_manager)
        job_nodes = self.job_context.job_nodes()
        for node in job_nodes[NodeType.CHIEF].values():
            node.status = NodeStatus.RUNNING
            self.job_context.update_job_node(node)

        for node in job_nodes[NodeType.WORKER].values():
            node.status = NodeStatus.RUNNING
            self.job_context.update_job_node(node)

        sync_name = "sync-0"
        job_nodes = self.job_context.job_nodes()
        for node in job_nodes[NodeType.CHIEF].values():
            sync_service.join_sync(sync_name, node.type, node.id)
        finished = sync_service.sync_finished(sync_name)
        self.assertFalse(finished)

        for node in job_nodes[NodeType.WORKER].values():
            sync_service.join_sync(sync_name, node.type, node.id)
        finished = sync_service.sync_finished(sync_name)
        self.assertTrue(finished)

    def test_barrier(self):
        mock_k8s_client()
        sync_service = SyncService(self.job_manager)
        barrier_name = "barrier-0"
        finished = sync_service.barrier(barrier_name)
        self.assertFalse(finished)
        sync_service.notify_barrier(barrier_name)
        finished = sync_service.barrier(barrier_name)
        self.assertTrue(finished)
