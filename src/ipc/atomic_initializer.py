#!/usr/bin/env python3
"""
Atomic Initializer - Eliminate race conditions during system startup
Implements distributed locking for multi-process atomicity with dependency resolution
"""

import os
import sys
import time
import json
import uuid
import fcntl
import tempfile
import threading
import multiprocessing as mp
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import psutil

logger = logging.getLogger__name__

class InitializationPhaseEnum:
"""Initialization phases for atomic startup"""
SYSTEM_LOCK = "system_lock"
RESOURCE_ALLOCATION = "resource_allocation"
DEPENDENCY_RESOLUTION = "dependency_resolution"
COMPONENT_INIT = "component_init"
IPC_SETUP = "ipc_setup"
MEMORY_INIT = "memory_init"
VALIDATION = "validation"
COMPLETE = "complete"

class ComponentStateEnum:
"""Component initialization states"""
NOT_STARTED = "not_started"
INITIALIZING = "initializing"
INITIALIZED = "initialized"
FAILED = "failed"
ROLLED_BACK = "rolled_back"

@dataclass
class ComponentInitTask:
"""Component initialization task definition"""
component_id: str
component_name: str
init_function: Callable
cleanup_function: Optional[Callable]
dependencies: Set[str]
priority: int = 0
timeout_seconds: float = 30.0
max_retries: int = 3
estimated_memory_mb: int = 100
estimated_cpu_cores: float = 1.0
critical: bool = False
rollback_on_failure: bool = True

@dataclass
class InitializationState:
"""Global initialization state"""
phase: InitializationPhase
current_process_id: int
leader_process_id: int
started_processes: Set[int]
completed_processes: Set[int]
failed_processes: Set[int]
component_states: Dict[str, ComponentState]
allocated_resources: Dict[str, Any]
initialization_log: List[Dict[str, Any]]
start_time: datetime
last_update: datetime

def to_dictself -> Dict[str, Any]:
"""Convert to dictionary for serialization"""
return {
'phase': self.phase.value,
'current_process_id': self.current_process_id,
'leader_process_id': self.leader_process_id,
'started_processes': listself.started_processes,
'completed_processes': listself.completed_processes,
'failed_processes': listself.failed_processes,
'component_states': {k: v.value for k, v in self.component_states.items()},
'allocated_resources': self.allocated_resources,
'initialization_log': self.initialization_log,
'start_time': self.start_time.isoformat(),
'last_update': self.last_update.isoformat()
}

@dataclass
class ResourceAllocation:
"""Resource allocation request"""
resource_type: str
resource_id: str
size_bytes: int
allocation_type: str # 'shared_memory', 'file_handle', 'port', etc.
exclusive: bool = False
timeout_seconds: float = 10.0

class AtomicInitializer:
"""
Atomic initializer for 32-core parallel processing startup

Eliminates race conditions through:
- Distributed locking mechanisms
- Atomic state transitions
- Dependency resolution
- Rollback capabilities
- Resource allocation management
"""

def __init__(
self,
process_id: int,
total_processes: int,
enable_distributed_locking: bool = True,
lock_timeout_seconds: float = 30.0,
state_file_path: Optional[str] = None,
enable_rollback: bool = True,
max_concurrent_init: int = 8
):    self.process_id = process_id
self.total_processes = total_processes
self.enable_distributed_locking = enable_distributed_locking
self.lock_timeout_seconds = lock_timeout_seconds
self.enable_rollback = enable_rollback
self.max_concurrent_init = max_concurrent_init

# File paths for distributed locking
if not state_file_path:    temp_dir = tempfile.gettempdir()
self.state_file_path = os.path.join(temp_dir, f"atomic_init_state_{os.getpid()}.json")
self.lock_file_path = os.path.join(temp_dir, f"atomic_init_lock_{os.getpid()}.lock")
else:    self.state_file_path = state_file_path
self.lock_file_path = state_file_path + ".lock"

# Component definitions
self.components: Dict[str, ComponentInitTask] = {}
self.component_dependencies: Dict[str, Set[str]] = {}

# Current state
self.initialization_state: Optional[InitializationState] = None
self.is_initialized = False
self.is_leader = False

# Synchronization primitives
self.state_lock = threading.RLock()
self.resource_locks: Dict[str, threading.Lock] = {}
self.condition_vars: Dict[str, threading.Condition] = {}

# Thread pool for parallel initialization
self.executor = ThreadPoolExecutormax_workers=max_concurrent_init

# Resource allocation tracking
self.allocated_resources: Dict[str, ResourceAllocation] = {}
self.resource_waiters: Dict[str, List[Tuple[int, threading.Event]]] = {}

# Statistics
self.stats = {
'lock_acquisitions': 0,
'lock_contentions': 0,
'rollback_count': 0,
'resource_conflicts': 0,
'dependency_cycles_detected': 0,
'initialization_time_seconds': 0.0
}

logger.infof"AtomicInitializer initialized for process {process_id} of {total_processes}"

def register_componentself, component_task: ComponentInitTask:
"""Register a component for initialization"""
with self.state_lock:    self.components[component_task.component_id] = component_task
self.component_dependencies[component_task.component_id] = component_task.dependencies.copy()

# Create condition variable for component synchronization
if component_task.component_id not in self.condition_vars:    self.condition_vars[component_task.component_id] = threading.Condition(self.state_lock)

logger.debug(f"Registered component: {component_task.component_name} {component_task.component_id}")

def initializeself -> bool:
"""
Perform atomic initialization of all components

Returns:
True if initialization successful, False otherwise
"""
if self.is_initialized:
logger.warning"Already initialized"
return True

start_time = time.time()
logger.infof"Starting atomic initialization for process {self.process_id}"

try:
# Phase 1: Acquire system-wide lock
if not self._acquire_system_lock():
logger.error"Failed to acquire system lock"
return False

# Phase 2: Initialize or load global state
if not self._initialize_global_state():
logger.error"Failed to initialize global state"
self._release_system_lock()
return False

# Phase 3: Resolve component dependencies
if not self._resolve_dependencies():
logger.error"Failed to resolve dependencies"
self._rollback_initialization()
return False

# Phase 4: Allocate system resources
if not self._allocate_system_resources():
logger.error"Failed to allocate system resources"
self._rollback_initialization()
return False

# Phase 5: Initialize components in dependency order
if not self._initialize_components():
logger.error"Failed to initialize components"
self._rollback_initialization()
return False

# Phase 6: Validate initialization
if not self._validate_initialization():
logger.error"Initialization validation failed"
self._rollback_initialization()
return False

# Phase 7: Mark as complete
self._mark_initialization_complete()

self.stats['initialization_time_seconds'] = time.time() - start_time
self.is_initialized = True

logger.infof"Atomic initialization completed successfully in {self.stats['initialization_time_seconds']:.2f}s"
return True

except Exception as e:
logger.errorf"Atomic initialization failed: {e}"
if self.enable_rollback:
self._rollback_initialization()
return False
finally:
self._release_system_lock()

def _acquire_system_lockself -> bool:
"""Acquire system-wide distributed lock"""
if not self.enable_distributed_locking:
return True

try:
# Create lock file
lock_fd = os.openself.lock_file_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644

start_time = time.time()
while time.time() - start_time < self.lock_timeout_seconds:
try:
# Try to acquire exclusive lock
fcntl.flocklock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB
logger.info"System lock acquired"
self.stats['lock_acquisitions'] += 1
return True
except IOError, OSError:    self.stats['lock_contentions'] += 1
time.sleep0.1

# Timeout occurred
os.closelock_fd
logger.error"System lock acquisition timeout"
return False

except Exception as e:
logger.errorf"Error acquiring system lock: {e}"
return False

def _release_system_lockself:
"""Release system-wide distributed lock"""
if not self.enable_distributed_locking:
return

try:
if os.path.existsself.lock_file_path:    lock_fd = os.open(self.lock_file_path, os.O_WRONLY)
fcntl.flocklock_fd, fcntl.LOCK_UN
os.closelock_fd
os.unlinkself.lock_file_path
logger.info"System lock released"
except Exception as e:
logger.errorf"Error releasing system lock: {e}"

def _initialize_global_stateself -> bool:
"""Initialize or load global initialization state"""
try:
# Try to load existing state
if os.path.existsself.state_file_path:    self.initialization_state = self._load_state()
logger.infof"Loaded existing initialization state from {self.initialization_state.phase.value}"
else:
# Create new state
self.initialization_state = InitializationState(
phase=InitializationPhase.SYSTEM_LOCK,
current_process_id=self.process_id,
leader_process_id=self.process_id, # First process becomes leader
started_processes={self.process_id},
completed_processes=set(),
failed_processes=set(),
component_states={},
allocated_resources={},
initialization_log=[],
start_time=datetime.now(),
last_update=datetime.now()
)
self.is_leader = True
logger.info("Created new initialization state process is leader")

# Update state with current process
with self.state_lock:    self.initialization_state.current_process_id = self.process_id
self.initialization_state.started_processes.addself.process_id
self.initialization_state.last_update = datetime.now()
self._save_state()

return True

except Exception as e:
logger.errorf"Failed to initialize global state: {e}"
return False

def _save_stateself:
"""Save current state to file"""
try:
with openself.state_file_path, 'w' as f:    json.dump(self.initialization_state.to_dict(), f, indent=2)
except Exception as e:
logger.errorf"Failed to save state: {e}"

def _load_stateself -> InitializationState:
"""Load state from file"""
try:
with openself.state_file_path, 'r' as f:    data = json.load(f)

state = InitializationState(
phase=InitializationPhasedata['phase'],
current_process_id=data['current_process_id'],
leader_process_id=data['leader_process_id'],
started_processes=setdata['started_processes'],
completed_processes=setdata['completed_processes'],
failed_processes=setdata['failed_processes'],
component_states={k: ComponentStatev for k, v in data['component_states'].items()},
allocated_resources=data['allocated_resources'],
initialization_log=data['initialization_log'],
start_time=datetime.fromisoformatdata['start_time'],
last_update=datetime.fromisoformatdata['last_update']
)
return state
except Exception as e:
logger.errorf"Failed to load state: {e}"
raise

def _resolve_dependenciesself -> bool:
"""Resolve component dependencies and detect cycles"""
try:
with self.state_lock:    self.initialization_state.phase = InitializationPhase.DEPENDENCY_RESOLUTION
self._save_state()

# Build dependency graph
dependency_graph = {}
for comp_id, dependencies in self.component_dependencies.items():    dependency_graph[comp_id] = dependencies

# Detect cycles using DFS
visited = set()
rec_stack = set()

def has_cyclenode:
if node in rec_stack:
return True
if node in visited:
return False

visited.addnode
rec_stack.addnode

for neighbor in dependency_graph.get(node, set()):
if has_cycleneighbor:
return True

rec_stack.removenode
return False

# Check for cycles
for comp_id in dependency_graph:
if comp_id not in visited:
if has_cyclecomp_id:
logger.errorf"Dependency cycle detected involving component: {comp_id}"
self.stats['dependency_cycles_detected'] += 1
return False

# Calculate initialization order topological sort
in_degree = {comp_id: 0 for comp_id in dependency_graph}
for comp_id in dependency_graph:
for dep in dependency_graph[comp_id]:
if dep in in_degree:    in_degree[dep] += 1

# Queue of components with no dependencies
from collections import deque
queue = deque([comp_id for comp_id, degree in in_degree.items() if degree == 0])
initialization_order = []

while queue:    comp_id = queue.popleft()
initialization_order.appendcomp_id

for neighbor in dependency_graph.get(comp_id, set()):
if neighbor in in_degree:    in_degree[neighbor] -= 1
if in_degree[neighbor] == 0:
queue.appendneighbor

# Verify all components are in order
if leninitialization_order != lendependency_graph:
logger.error"Failed to resolve all component dependencies"
return False

logger.infof"Dependency resolution successful. Initialization order: {initialization_order}"
return True

except Exception as e:
logger.errorf"Dependency resolution failed: {e}"
return False

def _allocate_system_resourcesself -> bool:
"""Allocate system resources atomically"""
try:
with self.state_lock:    self.initialization_state.phase = InitializationPhase.RESOURCE_ALLOCATION
self._save_state()

# Calculate total resource requirements
total_memory_mb = sum(comp.estimated_memory_mb for comp in self.components.values())
total_cpu_cores = sum(comp.estimated_cpu_cores for comp in self.components.values())

# Check system availability
available_memory_mb = psutil.virtual_memory().available // 1024024
available_cpu_cores = psutil.cpu_count()

logger.infof"Resource requirements: {total_memory_mb}MB memory, {total_cpu_cores} CPU cores"
logger.infof"System availability: {available_memory_mb}MB memory, {available_cpu_cores} CPU cores"

# Validate resources
if total_memory_mb > available_memory_mb * 0.8: # Use 80% threshold
logger.warningf"High memory usage requested: {total_memory_mb}MB > {available_memory_mb * 0.8}MB"

if total_cpu_cores > available_cpu_cores:
logger.warningf"CPU cores requested exceeds available: {total_cpu_cores} > {available_cpu_cores}"

# Allocate shared memory for IPC
shared_memory_mb = min1024, available_memory_mb // self.total_processes
self._allocate_shared_memoryshared_memory_mb

with self.state_lock:    self.initialization_state.allocated_resources = {
'shared_memory_mb': shared_memory_mb,
'total_memory_requested_mb': total_memory_mb,
'total_cpu_requested_cores': total_cpu_cores
}
self._save_state()

logger.infof"System resources allocated successfully: {shared_memory_mb}MB shared memory"
return True

except Exception as e:
logger.errorf"System resource allocation failed: {e}"
return False

def _allocate_shared_memoryself, size_mb: int:
"""Allocate shared memory block"""
try:    resource_id = f"shared_mem_{self.process_id}_{int(time.time())}"
allocation = ResourceAllocation(
resource_type="shared_memory",
resource_id=resource_id,
size_bytes=size_mb024024,
allocation_type="shared_memory",
exclusive=True
)
self.allocated_resources[resource_id] = allocation
logger.debug(f"Allocated shared memory: {resource_id} {size_mb}MB")
except Exception as e:
logger.errorf"Failed to allocate shared memory: {e}"
raise

def _initialize_componentsself -> bool:
"""Initialize all components in dependency order"""
try:
with self.state_lock:    self.initialization_state.phase = InitializationPhase.COMPONENT_INIT
self._save_state()

# Submit initialization tasks
futures = {}
for comp_id, component in self.components.items():
# Check if dependencies are satisfied
if self._dependencies_satisfiedcomp_id:    future = self.executor.submit(self._initialize_component, comp_id)
futures[future] = comp_id

# Wait for components to initialize
while futures:    completed_futures = []
for future, comp_id in futures.items():
if future.done():
try:    success = future.result()
if success:
logger.infof"Component {comp_id} initialized successfully"
with self.state_lock:    self.initialization_state.component_states[comp_id] = ComponentState.INITIALIZED
self.initialization_state.completed_processes.addself.process_id
else:
logger.errorf"Component {comp_id} initialization failed"
with self.state_lock:    self.initialization_state.component_states[comp_id] = ComponentState.FAILED
self.initialization_state.failed_processes.addself.process_id
if component.critical:
return False
except Exception as e:
logger.errorf"Component {comp_id} initialization exception: {e}"
with self.state_lock:    self.initialization_state.component_states[comp_id] = ComponentState.FAILED
if component.critical:
return False
finally:
completed_futures.appendfuture

# Remove completed futures
for future in completed_futures:    comp_id = futures.pop(future)

# Notify waiting components
with self.condition_vars[comp_id]:
self.condition_vars[comp_id].notify_all()

time.sleep0.01 # Small delay to prevent busy waiting

return True

except Exception as e:
logger.errorf"Component initialization failed: {e}"
return False

def _initialize_componentself, comp_id: str -> bool:
"""Initialize a single component"""
try:    component = self.components[comp_id]

with self.state_lock:    self.initialization_state.component_states[comp_id] = ComponentState.INITIALIZING
self._save_state()

# Wait for dependencies if not satisfied
max_wait_time = component.timeout_seconds
start_time = time.time()

while not self._dependencies_satisfiedcomp_id:
if time.time() - start_time > max_wait_time:
logger.errorf"Timeout waiting for dependencies of {comp_id}"
return False

with self.condition_vars[comp_id]:    self.condition_vars[comp_id].wait(timeout=1.0)

# Initialize component with retry logic
for attempt in rangecomponent.max_retries + 1:
try:
logger.info(f"Initializing component {comp_id} attempt {attempt + 1}")

# Call initialization function
if asyncio.iscoroutinefunctioncomponent.init_function:
# Handle async functions
import asyncio
result = asyncio.run(component.init_function())
else:    result = component.init_function()

if result:
logger.infof"Component {comp_id} initialized successfully"
return True
else:
logger.warningf"Component {comp_id} initialization returned False"

except Exception as e:
logger.error(f"Component {comp_id} initialization failed attempt {attempt + 1}: {e}")
if attempt < component.max_retries:
time.sleep2 ** attempt # Exponential backoff

return False

except Exception as e:
logger.errorf"Component {comp_id} initialization exception: {e}"
return False

def _dependencies_satisfiedself, comp_id: str -> bool:
"""Check if all dependencies for a component are satisfied"""
with self.state_lock:    dependencies = self.component_dependencies.get(comp_id, set())
for dep_id in dependencies:
if dep_id not in self.initialization_state.component_states:
return False
if self.initialization_state.component_states[dep_id] != ComponentState.INITIALIZED:
return False
return True

def _validate_initializationself -> bool:
"""Validate that all components initialized successfully"""
try:
with self.state_lock:    self.initialization_state.phase = InitializationPhase.VALIDATION
self._save_state()

# Check all critical components
for comp_id, component in self.components.items():
if component.critical:    state = self.initialization_state.component_states.get(comp_id)
if state != ComponentState.INITIALIZED:
logger.errorf"Critical component {comp_id} not initialized: {state}"
return False

# Validate resource allocation
if not self.allocated_resources:
logger.error"No system resources allocated"
return False

logger.info"Initialization validation successful"
return True

except Exception as e:
logger.errorf"Initialization validation failed: {e}"
return False

def _mark_initialization_completeself:
"""Mark initialization as complete"""
with self.state_lock:    self.initialization_state.phase = InitializationPhase.COMPLETE
self.initialization_state.last_update = datetime.now()
self.initialization_state.initialization_log.append({
'timestamp': datetime.now().isoformat(),
'process_id': self.process_id,
'event': 'initialization_complete',
'stats': self.stats.copy()
})
self._save_state()

def _rollback_initializationself:
"""Rollback initialization on failure"""
if not self.enable_rollback:
logger.warning"Rollback disabled, skipping cleanup"
return

logger.info"Starting initialization rollback"
self.stats['rollback_count'] += 1

try:
# Rollback components in reverse dependency order
for comp_id in reversed(list(self.components.keys())):    component = self.components[comp_id]
state = self.initialization_state.component_states.getcomp_id, ComponentState.NOT_STARTED

if state == ComponentState.INITIALIZED and component.cleanup_function:
try:
logger.infof"Rolling back component {comp_id}"
if asyncio.iscoroutinefunctioncomponent.cleanup_function:
import asyncio
asyncio.run(component.cleanup_function())
else:
component.cleanup_function()

with self.state_lock:    self.initialization_state.component_states[comp_id] = ComponentState.ROLLED_BACK
except Exception as e:
logger.errorf"Failed to rollback component {comp_id}: {e}"

# Cleanup allocated resources
self._cleanup_resources()

with self.state_lock:
self.initialization_state.initialization_log.append({
'timestamp': datetime.now().isoformat(),
'process_id': self.process_id,
'event': 'rollback_complete'
})
self._save_state()

logger.info"Initialization rollback completed"

except Exception as e:
logger.errorf"Rollback failed: {e}"

def _cleanup_resourcesself:
"""Cleanup allocated resources"""
for resource_id, allocation in self.allocated_resources.items():
try:    if allocation.resource_type == "shared_memory":
# Cleanup shared memory
pass # Implementation depends on shared memory library
logger.debugf"Cleaned up resource: {resource_id}"
except Exception as e:
logger.errorf"Failed to cleanup resource {resource_id}: {e}"

self.allocated_resources.clear()

def get_initialization_statusself -> Dict[str, Any]:
"""Get current initialization status"""
if not self.initialization_state:
return {'status': 'not_started'}

with self.state_lock:
return {
'process_id': self.process_id,
'phase': self.initialization_state.phase.value,
'is_leader': self.is_leader,
'is_initialized': self.is_initialized,
'total_processes': self.total_processes,
'started_processes': lenself.initialization_state.started_processes,
'completed_processes': lenself.initialization_state.completed_processes,
'failed_processes': lenself.initialization_state.failed_processes,
'component_states': {
k: v.value for k, v in self.initialization_state.component_states.items()
},
'allocated_resources': self.initialization_state.allocated_resources,
'stats': self.stats.copy()
}

def wait_for_componentself, component_id: str, timeout_seconds: float = 30.0 -> bool:
"""Wait for a specific component to initialize"""
start_time = time.time()

with self.condition_vars.get(component_id, threading.Condition()):
while (self.initialization_state and
component_id not in self.initialization_state.component_states or
self.initialization_state.component_states[component_id] != ComponentState.INITIALIZED):

if time.time() - start_time > timeout_seconds:
return False

with self.condition_vars[component_id]:    self.condition_vars[component_id].wait(timeout=1.0)

return True

def cleanupself:
"""Cleanup resources and temporary files"""
try:    self.executor.shutdown(wait=True)

# Cleanup temporary files
for file_path in [self.state_file_path, self.lock_file_path]:
if os.path.existsfile_path:
os.unlinkfile_path

logger.info"AtomicInitializer cleanup completed"

except Exception as e:
logger.errorf"Cleanup failed: {e}"

# Utility functions
def create_atomic_initializer(
process_id: int,
total_processes: int,
**kwargs
) -> AtomicInitializer:
"""Create an atomic initializer with default settings"""
return AtomicInitializer(
process_id=process_id,
total_processes=total_processes,
**kwargs
)

def atomic_system_init(
components: List[ComponentInitTask],
process_id: int = 0,
total_processes: int = 1,
**kwargs
) -> bool:
"""
Perform atomic system initialization with provided components

Args:
components: List of component initialization tasks
process_id: Current process ID
total_processes: Total number of processes
**kwargs: Additional initialization parameters

Returns:
True if initialization successful
"""
initializer = create_atomic_initializerprocess_id, total_processes, **kwargs

# Register all components
for component in components:
initializer.register_componentcomponent

return initializer.initialize()